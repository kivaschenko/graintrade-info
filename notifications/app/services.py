from typing import Dict, List
from .model import get_all_users_preferences, get_all_categories
from .schemas import PreferencesSchema, CategoryInResponse
from .rabbit_mq import ALL_TOPICS


def map_categories_to_topics_by_name(
    categories: List[CategoryInResponse], topics: Dict[int, str] = ALL_TOPICS
) -> Dict[str, str]:
    """
    Map user preferences to topics based on category names.
    """
    topics_by_name = {}  # {"Wheat 2 grade": "grain.wheat_2_grade"}
    for category in categories:
        topic = topics.get(category.id)
        if topic:
            topics_by_name[category.name] = topic
    return topics_by_name


async def get_all_users_by_topic_preferences() -> Dict[str, List[str]]:
    """
    Get all users preferences grouped by topic.
    Returns a dictionary where keys are topic names and values are lists of user emails.
    This is used to send bulk emails to users interested in specific topics.
    Returns:
        Dict[str, List[str]]: A dictionary mapping topic names to lists of user emails.
        Sample: {
            "grain.wheat_2_grade": ["user_test@example.com", "reciver-test@example.com"],}
    """
    user_preferences: List[PreferencesSchema] = await get_all_users_preferences()
    categories: List[CategoryInResponse] = await get_all_categories()

    topics_by_name = map_categories_to_topics_by_name(categories)

    topic_users: Dict[str, List[str]] = {}
    for preference in user_preferences:
        for category_name in preference.interested_categories:  # type: ignore
            # Get the topic by category name
            topic = topics_by_name.get(category_name)
            if topic:
                if topic not in topic_users:
                    topic_users[topic] = []
                topic_users[topic].extend([preference.email])  # type: ignore

    # Remove duplicates in each topic's user list
    for topic, users in topic_users.items():
        topic_users[topic] = list(set(users))

    # Return the final mapping of topics to user emails

    return topic_users
