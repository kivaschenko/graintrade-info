#!/bin/bash
# Force decimal point usage
export LC_NUMERIC=C

# Your authentication token
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJjaXZhc2NoZW5rbyIsInNjb3BlcyI6WyJtZSIsImNyZWF0ZTppdGVtIiwicmVhZDppdGVtIiwiZGVsZXRlOml0ZW0iLCJ2aWV3Om1hcCJdLCJ1c2VyX2lkIjoxLCJleHAiOjE3NDk4NDE0NTJ9.JbeLyjAIkVfeFLyS_M_IBsPVMaAvI0hHJvuajAfQEPA"

# Array of Ukrainian cities with their coordinates
declare -A cities=(
    ["Kyiv"]="50.4501,30.5234"
    ["Kharkiv"]="49.9935,36.2304"
    ["Dnipro"]="48.4647,35.0462"
    ["Odesa"]="46.4825,30.7233"
    ["Zaporizhzhia"]="47.8388,35.1396"
    ["Lviv"]="49.8397,24.0297"
    ["Cherkasy"]="49.4444,32.0598"
    ["Poltava"]="49.5883,34.5514"
    ["Vinnytsia"]="49.2331,28.4682"
    ["Khmelnytskyi"]="49.4220,26.9871"
)

# Array of grain types
declare -A grains=(
    ["Wheat"]="protein 12.5%, moisture 14%"
    ["Corn"]="moisture 14%, foreign matter 2%"
    ["Barley"]="protein 11%, moisture 14%"
    ["Sunflower"]="oil content 44%, moisture 8%"
    ["Soybean"]="protein 34%, moisture 12%"
)

# Array of prices
prices=(220 245 267 285 310 330 350 375 390 410)

# Array of amounts
amounts=(250 300 350 400 450 500 550 600 650 700)

# For each city
for city in "${!cities[@]}"; do
    # Get coordinates
    IFS=',' read -r lat lon <<< "${cities[$city]}"
    echo "Got coordinates: latitude ${lat} longitude ${lon}"
    lat=$(echo "$lat" | tr -d ' ' | tr ',' '.')
    lon=$(echo "$lon" | tr -d ' ' | tr ',' '.')
    
    # For each grain type
    for grain in "${!grains[@]}"; do
        # Add some randomness to coordinates (±0.5 degrees)
        lat_offset=$(awk 'BEGIN { srand(); printf "%.6f", rand()*0.5 - 0.25 }')
        lon_offset=$(awk 'BEGIN { srand(); printf "%.6f", rand()*0.5 - 0.25 }')
        
        # Calculate new coordinates with proper formatting
        new_lat=$(awk -v lat="$lat" -v offset="$lat_offset" 'BEGIN { printf "%.6f", lat + offset }')
        new_lon=$(awk -v lon="$lon" -v offset="$lon_offset" 'BEGIN { printf "%.6f", lon + offset }')
        
        # Random price and amount
        price=${prices[$RANDOM % ${#prices[@]}]}
        amount=${amounts[$RANDOM % ${#amounts[@]}]}
        
        echo "Creating item in ${city} at coordinates: ${new_lat},${new_lon}"
        
        # Send request with properly formatted coordinates
        http POST http://localhost:8000/items \
            user_id:=1 \
            category_id:=2 \
            offer_type="sell" \
            title="Sell ${grain}" \
            description="${grains[$grain]}" \
            price:=$price \
            currency="USD" \
            amount:=$amount \
            measure="metric ton" \
            terms_delivery="FCA" \
            country="Ukraine" \
            region="${city} Oblast" \
            latitude:=$new_lat \
            longitude:=$new_lon \
            "Authorization: Bearer ${TOKEN}"
            
        # Add a small delay to prevent overwhelming the server
        sleep 0.5
        
        # Print a separator for better readability
        echo "----------------------------------------"
    done
done