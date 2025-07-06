from xml.etree import ElementTree as ET

# Parse the KML file
with open("metadata/global_mining_extents_detailed.kml", 'rb') as file:
    tree = ET.parse(file)
    root = tree.getroot()

# KML namespace
ns = {"kml": "http://www.opengis.net/kml/2.2"}

# Find all placemarks
placemarks = root.findall(".//kml:Placemark", ns)
print(f"Found {len(placemarks)} placemarks")

# Loop over placemarks
for i, pm in enumerate(placemarks[:5]):  # Limit to 5 for brevity
    name = pm.find("kml:name", ns)
    print(f"\nPlacemark {i+1}")
    print(f"Name: {name.text if name is not None else 'No name'}")
    
    # Look for Polygon or MultiGeometry
    coords = pm.find(".//kml:coordinates", ns)
    if coords is not None:
        # Raw coordinates are like "lon,lat[,alt] lon,lat[,alt] ..."
        raw = coords.text.strip()
        coord_list = [tuple(map(float, pt.split(",")[:2])) for pt in raw.split()]
        
        # Print only the first few coordinates
        print("Coordinates (showing first 5 points):")
        for coord in coord_list[:5]:  # Print only first 5 coordinates
            print(coord)
    else:
        print("No coordinates found")

# After printing the coordinates, print all placemark names
print("\nAll placemark names:")
for pm in placemarks:
    name = pm.find("kml:name", ns)
    print(name.text if name is not None else "Unnamed")
