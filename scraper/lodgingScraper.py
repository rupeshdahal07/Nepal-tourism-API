"""
Setting Up the API
Create a Google Cloud Account:

Go to console.cloud.google.com
Sign up with your Google account
Create a Project:

In the Google Cloud Console, create a new project
Give it a name like "NepalTourismAPI"
Enable the Places API:

Navigate to "APIs & Services" > "Library"
Search for "Places API" and enable it
Set Up Billing:

You need to set up a billing account even for free tier usage
Google requires a credit card on file, but won't charge it unless you exceed the free tier
Create API Key:

Go to "APIs & Services" > "Credentials"
Click "Create credentials" > "API key"
Copy your new API key
Restrict Your API Key (Important!):

Set application and IP restrictions to prevent unauthorized usage
Restrict which APIs the key can access (Places API only)
"""

import requests
import json
import uuid
import time
from datetime import datetime

def get_nepal_lodgings_from_google():
    """Use Google Places API to get lodging data legally"""
    API_KEY = "YOUR_GOOGLE_API_KEY"  # Replace with your key
    
    # Nepal's major tourist destinations
    locations = [
        {"name": "Kathmandu", "lat": 27.7172, "lng": 85.3240},
        {"name": "Pokhara", "lat": 28.2096, "lng": 83.9856},
        {"name": "Namche Bazaar", "lat": 27.8069, "lng": 86.7140},
        {"name": "Chitwan National Park", "lat": 27.5291, "lng": 84.3542},
        {"name": "Lumbini", "lat": 27.4833, "lng": 83.2767}
    ]
    
    lodging_fixtures = []
    photo_fixtures = []
    
    for location in locations:
        print(f"Processing {location['name']}...")
        # Search for lodgings near this location
        url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={location['lat']},{location['lng']}&radius=5000&type=lodging&key={API_KEY}"
        
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Error getting data for {location['name']}: {response.status_code}")
            continue
        
        data = response.json()
        
        # Process each result
        for place in data.get('results', []):
            try:
                # Get detailed place information
                place_id = place['place_id']
                detail_url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=name,formatted_address,international_phone_number,website,rating,price_level,geometry,photos,types&key={API_KEY}"
                
                detail_response = requests.get(detail_url)
                if detail_response.status_code != 200:
                    continue
                
                place_details = detail_response.json().get('result', {})
                
                # Determine lodging type based on types and name
                lodging_type = 'hotel'  # Default
                name = place_details.get('name', '').lower()
                
                if 'guest_house' in place_details.get('types', []) or 'guesthouse' in name:
                    lodging_type = 'guesthouse'
                elif 'lodge' in name:
                    lodging_type = 'lodge'
                elif 'tea' in name and ('house' in name or 'shop' in name):
                    lodging_type = 'teahouse'
                
                # Generate price estimates based on price_level
                price_level = place_details.get('price_level', 2)
                price_ranges = {
                    0: (500, 1500),     # Budget
                    1: (1500, 3000),    # Economy
                    2: (3000, 7000),    # Mid-range
                    3: (7000, 15000),   # Upscale
                    4: (15000, 30000)   # Luxury
                }
                min_price, max_price = price_ranges.get(price_level, (3000, 7000))
                
                # Extract location information
                location_data = place_details.get('geometry', {}).get('location', {})
                latitude = location_data.get('lat', 0)
                longitude = location_data.get('lng', 0)
                
                # Determine amenities based on available data
                # (Google API doesn't provide amenities directly, would need to estimate)
                amenities = []
                if price_level >= 2:
                    amenities.extend(['wifi', 'restaurant'])
                if price_level >= 3:
                    amenities.extend(['room service', 'air conditioning'])
                
                # Generate UUID for this lodging
                lodging_id = str(uuid.uuid4())
                
                # Create lodging fixture
                lodging = {
                    "model": "api.lodging",
                    "pk": lodging_id,
                    "fields": {
                        "name": place_details.get('name', 'Unknown Lodging'),
                        "type": lodging_type,
                        "destination": None,  # Would need mapping to your destinations
                        "place": location['name'],
                        "latitude": latitude,
                        "longitude": longitude,
                        "phone": place_details.get('international_phone_number', ''),
                        "email": '',  # Not provided by Google Places
                        "website": place_details.get('website', ''),
                        "min_price": min_price,
                        "max_price": max_price,
                        "rating": place_details.get('rating'),
                        "amenities": amenities,
                        "booking_link": place_details.get('website', ''),
                        "availability": True,
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    }
                }
                
                lodging_fixtures.append(lodging)
                
                # Process photos if available
                photos = place_details.get('photos', [])[:3]  # Limit to 3 photos per place
                for i, photo in enumerate(photos):
                    photo_reference = photo.get('photo_reference')
                    if not photo_reference:
                        continue
                    
                    # Create photo fixture (we'd need to download these separately)
                    photo_fixture = {
                        "model": "api.lodgingphoto",
                        "pk": str(uuid.uuid4()),
                        "fields": {
                            "lodging": lodging_id,
                            "photo": f"lodgings/google_{lodging_id}_{i}.jpg",
                            "caption": f"Photo of {place_details.get('name')}"
                        }
                    }
                    
                    photo_fixtures.append({
                        "photo_reference": photo_reference,
                        "fixture": photo_fixture,
                        "filename": f"google_{lodging_id}_{i}.jpg"
                    })
                
            except Exception as e:
                print(f"Error processing place: {e}")
        
        # Handle pagination if needed
        while 'next_page_token' in data:
            # Sleep as the next_page_token needs time to activate
            time.sleep(2)
            
            next_page_url = f"{url}&pagetoken={data['next_page_token']}"
            next_response = requests.get(next_page_url)
            if next_response.status_code != 200:
                break
                
            data = next_response.json()
            # Process this page's results (similar to above)
            # ...
    
    # Save lodging fixtures
    with open('google_lodgings.json', 'w') as f:
        json.dump(lodging_fixtures, f, indent=2)
    
    # Download photos using the photo references
    download_google_photos(photo_fixtures, API_KEY)
    
    return lodging_fixtures

def download_google_photos(photo_data, api_key):
    """Download photos from Google Places API"""
    import os
    from PIL import Image
    from io import BytesIO
    
    # Create directory if it doesn't exist
    os.makedirs('media/lodgings', exist_ok=True)
    
    photo_fixtures = []
    
    for item in photo_data:
        photo_ref = item['photo_reference']
        fixture = item['fixture']
        filename = item['filename']
        
        # Build the URL to fetch the photo
        url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=1200&photoreference={photo_ref}&key={api_key}"
        
        try:
            response = requests.get(url)
            if response.status_code != 200:
                continue
                
            # Save image to file
            img = Image.open(BytesIO(response.content))
            img.save(f"media/lodgings/{filename}")
            
            # Add to fixtures list
            photo_fixtures.append(fixture)
            
            # Be nice to Google's servers
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Error downloading photo: {e}")
    
    # Save photo fixtures
    with open('google_lodging_photos.json', 'w') as f:
        json.dump(photo_fixtures, f, indent=2)

if __name__ == "__main__":
    get_nepal_lodgings_from_google()