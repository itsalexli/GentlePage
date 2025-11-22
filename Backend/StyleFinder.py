from bs4 import BeautifulSoup
import re
from collections import Counter
import os


def extract_colors_from_style(style_text):
    """Extract color values from CSS style text"""
    colors = []
    
    # Patterns for different color formats
    hex_pattern = r'#[0-9a-fA-F]{3,8}\b'
    rgb_pattern = r'rgba?\([^)]+\)'
    hsl_pattern = r'hsla?\([^)]+\)'
    color_names = r'\b(color|background-color|border-color|fill|stroke)\s*:\s*([a-z]+)\b'
    
    # Find hex colors
    colors.extend(re.findall(hex_pattern, style_text, re.IGNORECASE))
    
    # Find rgb/rgba colors
    colors.extend(re.findall(rgb_pattern, style_text, re.IGNORECASE))
    
    # Find hsl/hsla colors
    colors.extend(re.findall(hsl_pattern, style_text, re.IGNORECASE))
    
    # Find named colors (like 'red', 'blue', etc.)
    named_colors = re.findall(color_names, style_text, re.IGNORECASE)
    colors.extend([color[1] for color in named_colors if color[1] not in ['inherit', 'initial', 'unset', 'transparent', 'currentColor']])
    
    return colors


def extract_fonts_from_style(style_text):
    """Extract font-family values from CSS style text"""
    fonts = []
    
    # Pattern for font-family
    font_pattern = r'font-family\s*:\s*([^;]+)'
    
    matches = re.findall(font_pattern, style_text, re.IGNORECASE)
    for match in matches:
        # Split by comma and clean up
        font_list = [font.strip().strip('"').strip("'") for font in match.split(',')]
        fonts.extend(font_list)
    
    return fonts


def analyze_styles(file_path):
    """
    Analyze HTML file to extract common fonts and colors
    
    Args:
        file_path: Path to the HTML file to analyze
    
    Returns:
        Dictionary with fonts and colors analysis
    """
    
    # Read the HTML file
    with open(file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()
    
    # Parse with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    all_colors = []
    all_fonts = []
    
    # 1. Extract from <style> tags
    print("Analyzing <style> tags...")
    for style_tag in soup.find_all('style'):
        style_text = style_tag.string or ''
        all_colors.extend(extract_colors_from_style(style_text))
        all_fonts.extend(extract_fonts_from_style(style_text))
    
    # 2. Extract from inline styles
    print("Analyzing inline styles...")
    for element in soup.find_all(style=True):
        style_text = element.get('style', '')
        all_colors.extend(extract_colors_from_style(style_text))
        all_fonts.extend(extract_fonts_from_style(style_text))
    
    # 3. Extract from link tags (external stylesheets - just the reference)
    print("Analyzing external stylesheet references...")
    external_stylesheets = []
    for link in soup.find_all('link', rel='stylesheet'):
        href = link.get('href', '')
        if href:
            external_stylesheets.append(href)
    
    # 4. Extract colors from SVG elements
    print("Analyzing SVG elements...")
    for svg in soup.find_all('svg'):
        # Check fill and stroke attributes
        if svg.get('fill'):
            all_colors.append(svg.get('fill'))
        if svg.get('stroke'):
            all_colors.append(svg.get('stroke'))
        
        # Check all child elements
        for element in svg.find_all():
            if element.get('fill'):
                all_colors.append(element.get('fill'))
            if element.get('stroke'):
                all_colors.append(element.get('stroke'))
    
    # Count occurrences
    color_counter = Counter(all_colors)
    font_counter = Counter(all_fonts)
    
    # Remove generic/system fonts for cleaner output
    generic_fonts = ['serif', 'sans-serif', 'monospace', 'cursive', 'fantasy', 'system-ui']
    font_counter = Counter({font: count for font, count in font_counter.items() 
                           if font.lower() not in generic_fonts})
    
    # Remove 'none' and 'transparent' from colors
    color_counter = Counter({color: count for color, count in color_counter.items() 
                            if color.lower() not in ['none', 'transparent', 'inherit', 'currentcolor']})
    
    return {
        'colors': color_counter,
        'fonts': font_counter,
        'external_stylesheets': external_stylesheets
    }


def print_analysis(results):
    """Print the analysis results in a formatted way"""
    
    print("\n" + "="*60)
    print("STYLE ANALYSIS RESULTS")
    print("="*60)
    
    # Print Fonts
    print("\n📝 COMMON FONTS:")
    print("-" * 60)
    if results['fonts']:
        # Sort by count, descending
        sorted_fonts = results['fonts'].most_common(15)  # Top 15 fonts
        for i, (font, count) in enumerate(sorted_fonts, 1):
            print(f"{i:2d}. {font:<40} ({count:>3} occurrences)")
    else:
        print("No fonts found in the HTML file.")
    
    # Print Colors
    print("\n🎨 COMMON COLORS:")
    print("-" * 60)
    if results['colors']:
        # Sort by count, descending
        sorted_colors = results['colors'].most_common(20)  # Top 20 colors
        for i, (color, count) in enumerate(sorted_colors, 1):
            print(f"{i:2d}. {color:<40} ({count:>3} occurrences)")
    else:
        print("No colors found in the HTML file.")
    
    # Print External Stylesheets
    if results['external_stylesheets']:
        print("\n🔗 EXTERNAL STYLESHEETS:")
        print("-" * 60)
        for i, stylesheet in enumerate(results['external_stylesheets'], 1):
            print(f"{i:2d}. {stylesheet}")
    
    print("\n" + "="*60)
    print(f"Total unique fonts: {len(results['fonts'])}")
    print(f"Total unique colors: {len(results['colors'])}")
    print(f"Total external stylesheets: {len(results['external_stylesheets'])}")
    print("="*60 + "\n")


def save_to_file(results, output_file):
    """Save analysis results to a file"""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("="*60 + "\n")
        f.write("STYLE ANALYSIS RESULTS\n")
        f.write("="*60 + "\n\n")
        
        # Fonts
        f.write("COMMON FONTS:\n")
        f.write("-" * 60 + "\n")
        if results['fonts']:
            sorted_fonts = results['fonts'].most_common()
            for i, (font, count) in enumerate(sorted_fonts, 1):
                f.write(f"{i:2d}. {font:<40} ({count:>3} occurrences)\n")
        else:
            f.write("No fonts found.\n")
        
        # Colors
        f.write("\n\nCOMMON COLORS:\n")
        f.write("-" * 60 + "\n")
        if results['colors']:
            sorted_colors = results['colors'].most_common()
            for i, (color, count) in enumerate(sorted_colors, 1):
                f.write(f"{i:2d}. {color:<40} ({count:>3} occurrences)\n")
        else:
            f.write("No colors found.\n")
        
        # External Stylesheets
        if results['external_stylesheets']:
            f.write("\n\nEXTERNAL STYLESHEETS:\n")
            f.write("-" * 60 + "\n")
            for i, stylesheet in enumerate(results['external_stylesheets'], 1):
                f.write(f"{i:2d}. {stylesheet}\n")
        
        f.write("\n" + "="*60 + "\n")
        f.write(f"Total unique fonts: {len(results['fonts'])}\n")
        f.write(f"Total unique colors: {len(results['colors'])}\n")
        f.write(f"Total external stylesheets: {len(results['external_stylesheets'])}\n")
        f.write("="*60 + "\n")


def main():
    """Main function to run the style analyzer"""
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    input_file = os.path.join(script_dir, 'Sample.txt')
    output_file = os.path.join(script_dir, 'style_analysis.txt')
    
    print(f"Analyzing styles from {input_file}...")
    print("This may take a moment for large files...\n")
    
    try:
        # Analyze the HTML
        results = analyze_styles(input_file)
        
        # Print results to console
        print_analysis(results)
        
        # Save to file
        save_to_file(results, output_file)
        print(f"✓ Detailed analysis saved to {output_file}")
        
    except FileNotFoundError:
        print(f"Error: Could not find {input_file}")
        print("Make sure Sample.txt exists in the Backend directory.")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
