import rasterio
import numpy as np
import matplotlib.pyplot as plt
import os
from pathlib import Path
import glob

# Create output directory
os.makedirs("data/rgb", exist_ok=True)

def rescale(x, min_val=0, max_val=2000):
    """Rescale reflectance values to [0, 1] range"""
    x = np.clip(x, min_val, max_val)
    return (x - min_val) / (max_val - min_val)

def process_image(image_path):
    """Process a single image to generate RGB visualization"""
    try:
        with rasterio.open(image_path) as src:
            # Read bands 3-2-1 for RGB
            red = src.read(3).astype(np.float32)
            green = src.read(2).astype(np.float32)
            blue = src.read(1).astype(np.float32)
            
            # Create RGB composite
            rgb = np.dstack([
                rescale(red),
                rescale(green),
                rescale(blue)
            ])
            
            # Generate output filename
            output_filename = os.path.basename(image_path).replace('.tif', '.png')
            output_path = os.path.join("data/rgb", output_filename)
            
            # Save RGB image
            plt.imsave(output_path, rgb)
            print(f"✅ Generated RGB visualization: {output_path}")
            
    except Exception as e:
        print(f"❌ Error processing {image_path}: {str(e)}")

def main():
    # Get all tif files in data/images
    image_files = glob.glob("data/images/**/*.tif", recursive=True)
    total_files = len(image_files)
    
    print(f"\n=== Processing {total_files} images ===")
    
    # Process each image
    for idx, image_path in enumerate(image_files, 1):
        print(f"\nProcessing image {idx}/{total_files}: {image_path}")
        process_image(image_path)
    
    print("\n=== RGB visualization generation completed! ===")

if __name__ == "__main__":
    main() 