from typing import Annotated, List, Optional
import logging

from fastapi import (
    Depends,
    HTTPException,
    status,
    BackgroundTasks,
    APIRouter,
    File,
    UploadFile,
    Query,
)
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse, FileResponse

import jwt
import tempfile
import os

from ..schemas import (
    ItemInDB,
    ItemInResponse,
    ItemsByUserResponse,
    CategoryInResponse,
)
from ..models import items_model, subscription_model, tarif_model, category_model
from ..service_layer import item_services
from . import JWT_SECRET

router = APIRouter(tags=["Items"])
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={
        "me": "Read information about the current user.",
        "create:item": "Allowed to create a new Item",
        "read:item": "Allowed to read items.",
        "delete:item": "Allowed to delete item.",
        "add:category": "Allowed to add a new Category",
        "view:map": "Allowed to view map.",
        "import:export": "Allowed to import/export data via Excel/CSV.",
    },
)

# Logging configuration
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


# ==========
# Dependency


async def get_current_user_id(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id: str = payload.get("user_id")
        scopes: str = payload.get("scopes")
        if user_id is None:
            logging.error("No user_id found in token")
            raise credentials_exception
    except jwt.PyJWTError as e:
        logging.error(e)
        raise credentials_exception
    return user_id, scopes


# ------------------
# Items endpoints


@router.post("/items", response_model=ItemInResponse, status_code=201, tags=["Items"])
async def create_item(
    item: ItemInDB,
    background_tasks: BackgroundTasks,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    if token is None or token == "null" or token == "":
        logging.error("No token provided")
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id, scopes = await get_current_user_id(token)
    # check scope and permissions here
    if "create:item" not in scopes:
        logging.error("Not enough permissions")
        raise HTTPException(status_code=403, detail="Not enough permissions")
    usage_info = await subscription_model.get_subscription_usage_for_user(int(user_id))
    counter_usage = usage_info.get("items_count")
    scope = usage_info.get("tarif_scope")
    tarif = await tarif_model.get_tarif_by_scope(scope)
    counter_limit = tarif.__getattribute__("items_limit")
    if counter_usage >= counter_limit:
        logging.error("Not enough permissions, limit reached")
        raise HTTPException(
            status_code=403, detail="Not enough permissions, service limit reached"
        )
    new_item = await items_model.create(item=item, user_id=int(user_id))
    if new_item is None:
        logging.error("Item not created")
        raise HTTPException(status_code=400, detail="Item not created")
    # Extend new Item with ctagories name, ua_name etc.
    new_item.user_id = int(user_id)
    # Get category by id
    category: CategoryInResponse = await category_model.get_by_id(
        category_id=item.category_id
    )
    new_item.category_name = category.name
    new_item.category_ua_name = category.ua_name
    logging.info(f"New item created: {new_item}")
    background_tasks.add_task(item_services.send_item_to_queue, new_item)
    return new_item


@router.post(
    "/create-batches-item",
    response_model=List[ItemInResponse],
    status_code=201,
    tags=["Items"],
)
async def create_items_batch(
    items: List[ItemInDB],
    token: Annotated[str, Depends(oauth2_scheme)],
):
    """Create multiple items in a single request for the authenticated user."""
    if token is None or token == "null" or token == "":
        logging.error("No token provided")
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id, scopes = await get_current_user_id(token)
    if "create:item" not in scopes:
        logging.error("Not enough permissions")
        raise HTTPException(status_code=403, detail="Not enough permissions")
    try:
        created = await items_model.create_batch(items=items, user_id=int(user_id))
        for it in created:
            it.user_id = user_id  # type: ignore
        return created
    except Exception as e:
        logging.error(f"Error in create_items_batch: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/items", status_code=200, tags=["Items"])
async def read_items(
    offset: int = 0,
    limit: int = 10,
    token: Annotated[str, Depends(oauth2_scheme)] = "null",
):
    """Get all items with count value"""
    if limit > 100:
        logging.error(f"The number of limit excited: {limit}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Limit of items excited."
        )
    try:
        # Add map access permission check
        if token != "null":
            _, scopes = await get_current_user_id(token)
            has_map_access = "view:map" in scopes
        else:
            has_map_access = False
        # Get items and count value
        items, total_items = await items_model.get_all(offset=offset, limit=limit)
        return {
            "items": items,
            "total_items": total_items,
            "has_map_access": has_map_access,
        }
    except Exception as e:
        logging.error(f"Error in read_items: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get(
    "/items/{item_id}", response_model=ItemInResponse, status_code=200, tags=["Items"]
)
async def read_item(
    item_id: int, token: Annotated[str, Depends(oauth2_scheme)] = "null"
):
    """Return certain item's info."""
    try:
        db_item = await items_model.get_by_id(item_id)
        if db_item is None:
            logging.error(f"Item with id {item_id} not found")
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Item not found")
        # If token is provided, verify permisiion and increment map views
        if token != "null":
            user_id, scopes = await get_current_user_id(token)
            if "read:item" not in scopes:
                raise HTTPException(status.HTTP_403_FORBIDDEN)
        # Get Category data
        # Already realized in items_model
        category = await category_model.get_by_id(db_item.category_id)
        if category:
            db_item.category_name = category.name
            db_item.category_ua_name = category.ua_name
        else:
            logging.warning(f"Category with id {db_item.category_id} not found")
            db_item.category_name = "Unknown"
            db_item.category_ua_name = "Невідомо"
        logging.info(f"Item read successfully: {db_item}")
        return db_item
    except Exception as e:
        logging.error(f"Error in read_item: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.delete(
    "/items/{item_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    tags=["Items"],
)
async def delete_item_bound_to_user(
    item_id: int,
    token: Annotated[
        str, Depends(oauth2_scheme)
    ] = "null",  # Default to 'null' if no token is provided
    background_tasks: BackgroundTasks = None,
):
    """Delete an item by its ID, only if the user has the 'delete:item' scope."""
    if token == "null":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="No token provided"
        )
    try:
        user_id, scopes = await get_current_user_id(token)
        if "delete:item" not in scopes:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
        # Get telegram message_id and chat_id before deleting the item
        telegram_message_id, chat_id = await items_model.get_item_telegram_message(
            item_id
        )
        if telegram_message_id is None or chat_id is None:
            telegram_message_id = 0
            chat_id = 0
        # Proceed to delete the item
        await items_model.delete(item_id, int(user_id))
        background_tasks.add_task(
            item_services.send_deleted_item_to_queue,
            item_id=item_id,
            telegram_message_id=telegram_message_id,
            chat_id=chat_id,
        )
        logging.info(f"Item with id {item_id} deleted by user {user_id}")
        return {"status": "success", "message": "Item deleted successfully"}
    except Exception as e:
        return {"status": "error", "message": f"Something went wrong: {e}"}


@router.get(
    "/items-by-user/{user_id}", response_model=ItemsByUserResponse, tags=["Items"]
)
async def read_items_by_user(
    user_id: int,
    offset: int = 0,
    limit: int = 10,
    token: Annotated[
        str, Depends(oauth2_scheme)
    ] = "null",  # Default to 'null' if no token is provided,
):
    """Return all items created by a specific user."""
    try:
        if token == "null":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="No token provided"
            )
        _, scopes = await get_current_user_id(token)
        if "read:item" not in scopes:
            raise HTTPException(status.HTTP_403_FORBIDDEN)
        items, total_items = await items_model.get_items_by_user_id(
            user_id=user_id, offset=offset, limit=limit
        )
        return {"items": items, "total_items": total_items}
    except Exception as e:
        logging.error(f"Error read items by user_id: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get(
    "/find-items-in-distance",
    response_model=List[ItemInResponse],
    tags=["filter items"],
)
async def find_items_in_radius(
    latitude: float,
    longitude: float,
    distance: int,  # in meters
):
    """Find all items within a given distance from a given point. The distance is in meters."""
    return await items_model.find_in_distance(
        longitude=longitude, latitude=latitude, distance=distance
    )


@router.get("/filter-items", response_model=List[ItemInResponse], tags=["filter items"])
async def filter_items(
    min_price: float = 0.0,
    max_price: float = 999999.0,
    currency: str = "UAH",
    min_amount: int = 0,
    max_amount: int = 999999,
    measure: str = "",
    terms_delivery: str = "",
    country: str = "",
    region: str = "",
):
    return await items_model.get_filtered_items(
        min_price=min_price,
        max_price=max_price,
        currency=currency,
        min_amount=min_amount,
        max_amount=max_amount,
        measure=measure,
        terms_delivery=terms_delivery,
        country=country,
        region=region,
    )


@router.get("/items-geojson", response_model=dict, tags=["Items"])
async def get_items_geojson(
    category_id: Optional[int] = None,
    offer_type: Optional[str] = "all",
    min_price: Optional[int] = 0,
    max_price: Optional[int] = 999999,
    country: Optional[str] = "all",
    currency: Optional[str] = "all",
    incoterm: Optional[str] = "all",
    token: Annotated[str, Depends(oauth2_scheme)] = "null",
):
    """Get filtered items with geo information.
    GET /items-geojson?category_id=32&offer_type=buy&min_price=12000&country=Ukraine&currency=uah&incoterm=DAP HTTP/1.1
    """
    try:
        # Optionally, add scope check here if only authorized users can view the full map
        _, scopes = await get_current_user_id(token)
        if "view:map" not in scopes:  # Example scope check
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

        items = await items_model.get_filtered_items_geo_json(
            category_id=category_id,
            offer_type=offer_type,
            min_price=min_price,
            max_price=max_price,
            country=country,
            currency=currency,
            incoterm=incoterm,
        )
        return {"status": "success", "items": items}
    except Exception as e:
        logging.error(f"Error in get_all_items_geojson: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/countries", response_model=dict, tags=["Items"])
async def get_countries():
    try:
        countries = await items_model.get_countries_list()
        return {"status": "success", "countries": countries}
    except Exception as e:
        logging.error(f"Error during countris list getting: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


# ------------------
# Import/Export endpoints (Business plan only)


@router.post("/items/import", response_model=dict, tags=["Items", "Import/Export"])
async def import_items_from_file(
    file: UploadFile = File(...),
    token: Annotated[str, Depends(oauth2_scheme)] = "null",
):
    """Import items from CSV/Excel file. Requires Business plan subscription."""
    if token is None or token == "null" or token == "":
        logging.error("No token provided")
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id, scopes = await get_current_user_id(token)

    # Check for import/export scope (Business plan only)
    if "import:export" not in scopes:
        logging.error("Import/export requires Business plan subscription")
        raise HTTPException(
            status_code=403,
            detail="Import/export functionality requires Business plan subscription",
        )

    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in {"csv", "xls", "xlsx"}:
        raise HTTPException(
            status_code=400, detail="Only .csv, .xls and .xlsx files are supported"
        )

    try:
        # Read file content
        contents = await file.read()

        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

        # Parse file (this would integrate with the existing parsers service)
        # For now, return a placeholder response
        # In a real implementation, you would:
        # 1. Parse the file using the existing parser service
        # 2. Validate the data
        # 3. Create items in batch using existing create_items_batch logic

        return {
            "status": "success",
            "message": f"File {file.filename} uploaded successfully",
            "file_type": file_ext,
            "user_id": user_id,
            "note": "Import functionality requires integration with parser service",
        }

    except Exception as e:
        logging.error(f"Error during file import: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing import file",
        )
    finally:
        # Clean up temporary file
        if "tmp_path" in locals():
            try:
                os.remove(tmp_path)
            except Exception:
                pass


@router.get("/items/export", response_model=dict, tags=["Items", "Import/Export"])
async def export_items_to_file(
    format: str = Query("csv", enum=["csv", "xls"]),
    user_items_only: bool = Query(
        False, description="Export only current user's items"
    ),
    token: Annotated[str, Depends(oauth2_scheme)] = "null",
):
    """Export items to CSV/Excel file. Requires Business plan subscription."""
    if token is None or token == "null" or token == "":
        logging.error("No token provided")
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id, scopes = await get_current_user_id(token)

    # Check for import/export scope (Business plan only)
    if "import:export" not in scopes:
        logging.error("Import/export requires Business plan subscription")
        raise HTTPException(
            status_code=403,
            detail="Import/export functionality requires Business plan subscription",
        )

    try:
        # Get items to export
        if user_items_only:
            items, _ = await items_model.get_items_by_user_id(
                user_id=int(user_id),
                offset=0,
                limit=10000,  # High limit for export
            )
        else:
            items, _ = await items_model.get_all(offset=0, limit=10000)

        # For now, return metadata about what would be exported
        # In a real implementation, you would:
        # 1. Convert items to CSV/Excel format
        # 2. Create downloadable file
        # 3. Return FileResponse with the generated file

        return {
            "status": "success",
            "message": f"Export ready in {format} format",
            "items_count": len(items),
            "format": format,
            "user_items_only": user_items_only,
            "user_id": user_id,
            "note": "Export functionality requires file generation implementation",
        }

    except Exception as e:
        logging.error(f"Error during export: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing export request",
        )


@router.get("/items/template", response_model=dict, tags=["Items", "Import/Export"])
async def get_import_template(
    format: str = Query("csv", enum=["csv", "xls"]),
    token: Annotated[str, Depends(oauth2_scheme)] = "null",
):
    """Download template file for importing items. Requires Business plan subscription."""
    if token is None or token == "null" or token == "":
        logging.error("No token provided")
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id, scopes = await get_current_user_id(token)

    # Check for import/export scope (Business plan only)
    if "import:export" not in scopes:
        logging.error("Import/export requires Business plan subscription")
        raise HTTPException(
            status_code=403,
            detail="Import/export functionality requires Business plan subscription",
        )

    try:
        # Return template information
        # In a real implementation, you would return a FileResponse with the template
        return {
            "status": "success",
            "message": f"Template available in {format} format",
            "format": format,
            "fields": [
                "category_id",
                "offer_type",
                "title",
                "description",
                "price",
                "currency",
                "amount",
                "measure",
                "terms_delivery",
                "country",
                "region",
                "latitude",
                "longitude",
            ],
            "note": "Template download requires file generation implementation",
        }

    except Exception as e:
        logging.error(f"Error getting template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting template",
        )
