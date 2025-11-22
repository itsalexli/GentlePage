from bs4 import BeautifulSoup
import re

def clean_html(file_path):
    """
    Clean HTML file by removing unnecessary elements while preserving content structure.
    
    IMPORTANT: This cleaner preserves ALL navigation elements including:
    - <nav> tags and all their contents
    - <header> elements that contain navigation
    - Navigation menus, dropdowns, and hamburger menus
    - Elements with IDs like 'nav-header', 'sl-nav', 'menuOpen', etc.
    - Navigation-related classes and structure
    
    Args:
        file_path: Path to the HTML file to clean
    
    Returns:
        Cleaned HTML as a string
    """
    
    # Read the HTML file
    with open(file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()
    
    # Parse with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Helper function to check if element is inside navigation
    def is_in_navigation(element):
        """Check if element is inside any navigation-related parent"""
        parent = element.parent
        while parent:
            if parent.name in ['nav', 'header']:
                return True
            if parent.get('class'):
                classes = ' '.join(parent.get('class', []))
                if any(nav_class in classes for nav_class in ['nav', 'navigation', 'menu', 'navbar', 'sl-nav', 'offcanvas']):
                    return True
            if parent.get('id') in ['nav-header', 'sl-nav', 'sl-header-offcanvas', 'menuOpen', 'menuClose']:
                return True
            parent = parent.parent
        return False
    
    # Remove unwanted elements (but preserve nav elements and navigation-related headers)
    unwanted_tags = [
        'style',           # Remove all style tags
        'footer',          # Remove footers
        'iframe',          # Remove iframes
        'noscript',        # Remove noscript tags
    ]
    
    for tag in unwanted_tags:
        for element in soup.find_all(tag):
            element.decompose()
    
    # Remove header elements ONLY if they don't contain navigation
    for header_element in soup.find_all('header'):
        # Keep headers that contain nav elements or have navigation-related classes
        has_nav = header_element.find('nav') is not None
        has_nav_class = any(nav_class in ' '.join(header_element.get('class', [])) 
                           for nav_class in ['nav', 'navigation', 'menu', 'header-nav'])
        
        # Only remove if it's not navigation-related
        if not has_nav and not has_nav_class:
            header_element.decompose()
    
    # Keep all navigation elements - do not remove nav bars
    
    # Remove tracking and analytics scripts
    for script in soup.find_all('script'):
        src = script.get('src', '')
        script_id = script.get('id', '')
        # Remove analytics/tracking scripts
        if any(tracker in src.lower() for tracker in [
            'analytics', 'gtag', 'google-analytics', 'googletagmanager',
            'facebook.net', 'fbevents', 'connect.facebook',
            'linkedin.com', 'li.lms-analytics',
            'reddit', 'pixel',
            'pinterest', 'pintrk',
            'tiq.sunlife', 'utag', 'tealium',
            'cookielaw', 'onetrust',
            'decibelinsight',
            'go-mpulse', 'boomerang',
            'chrome-extension://',
            'coveo'
        ]) or 'utag' in script_id or 'BOOMR' in script.get_text():
            script.decompose()
        # Remove JSON-LD structured data
        elif script.get('type') == 'application/ld+json':
            script.decompose()
        # Remove inline tracking code
        elif any(keyword in script.get_text() for keyword in ['utag_data', 'fbq(', 'gtag(', '_linkedin_data_partner_ids']):
            script.decompose()
    
    # Remove browser extension elements
    for element in soup.find_all(['grammarly-desktop-integration', 'simplify-jobs-page-script']):
        element.decompose()
    
    # Remove elements with extension-related classes/ids
    for element in soup.find_all(attrs={'class': re.compile('apolloio|extension-opener|simplify-jobs')}):
        element.decompose()
    
    # Remove preload/prefetch links (performance hints)
    for link in soup.find_all('link', rel=['preload', 'prefetch']):
        link.decompose()
    
    # Remove meta tags except charset and viewport
    for meta in soup.find_all('meta'):
        if not (meta.get('charset') or meta.get('name') in ['viewport', 'charset']):
            meta.decompose()
    
    # Remove canonical and alternate language links (SEO metadata)
    for link in soup.find_all('link', rel=['canonical', 'alternate']):
        link.decompose()
    
    # Remove elements by class/id (cookie banners only - preserve ALL navigation)
    # Remove by ID (cookie/consent elements only, NOT navigation)
    for element_id in ['onetrust-consent-sdk', 'onetrust-banner-sdk', 'onetrust-pc-sdk']:
        element = soup.find(id=element_id)
        if element:
            element.decompose()
    
    # Remove specific navigation/cookie classes without removing dropdown content
    for class_name in ['cookie', 'banner']:
        for element in soup.find_all(class_=class_name):
            element.decompose()
    
    # Remove elements with aria-hidden="true" ONLY if they don't contain substantial text
    # This preserves hidden dropdown content while removing decorative elements
    # IMPORTANT: Never remove SVG icons even if aria-hidden="true"
    for element in soup.find_all(attrs={'aria-hidden': 'true'}):
        # Skip SVG elements and elements inside navigation
        if element.name == 'svg' or is_in_navigation(element):
            continue
        text_content = element.get_text(strip=True)
        # Only remove if it has no meaningful text (less than 10 characters)
        if len(text_content) < 10:
            element.decompose()
    
    # Remove elements with display:none ONLY if they don't contain substantial text
    # This preserves dropdown content while removing empty hidden containers
    for element in soup.find_all(style=True):
        style_value = element.get('style', '').lower()
        if re.search(r'display\s*:\s*none', style_value):
            text_content = element.get_text(strip=True)
            # Only remove if it has no meaningful text (less than 10 characters)
            if len(text_content) < 10:
                element.decompose()
    
    # Remove inline styles EXCEPT in navigation elements
    for tag in soup.find_all(True):
        # Preserve styles in navigation elements
        if not is_in_navigation(tag) and tag.has_attr('style'):
            del tag['style']
        
        # Clean up other unnecessary attributes (keeping class for structure)
        # NOTE: We preserve essential attributes like href, src, action, type, name, value, 
        # id, placeholder, required, etc. that are needed for links, forms, and inputs to work
        # IMPORTANT: We now preserve Bootstrap data attributes in navigation (data-bs-*)
        attrs_to_remove = ['data-sl-aem-component', 'data-sl-component', 'data-cmp-hook-accordion', 
                          'data-class', 'data-class-icon', 
                          'data-parsley-validate', 'data-parsley-error-message',
                          'data-parsley-id', 'data-parsley-pattern', 'data-parsley-pattern-message',
                          'data-parsley-required', 'data-parsley-required-message', 'data-single-expansion',
                          'data-title', 'data-cy', 'data-grammarly-shadow-root']
        
        # Only remove Font Awesome data attributes if NOT in navigation
        if not is_in_navigation(tag):
            attrs_to_remove.extend(['data-fa-i2svg', 'data-icon', 'data-prefix'])
        
        # Only remove Bootstrap data attributes if NOT in navigation
        if not is_in_navigation(tag):
            attrs_to_remove.extend(['data-bs-target', 'data-bs-toggle', 'data-bs-dismiss'])
        
        for attr in attrs_to_remove:
            if tag.has_attr(attr):
                del tag[attr]
    
    # Remove empty divs and spans (but preserve SVG containers and navigation elements)
    for tag in soup.find_all(['div', 'span']):
        # Don't remove if it's in navigation or contains SVG
        if is_in_navigation(tag) or tag.find('svg'):
            continue
        # Remove if empty and doesn't contain important elements
        if not tag.get_text(strip=True) and not tag.find_all(['img', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'svg']):
            tag.decompose()
    
    # Get the cleaned HTML
    cleaned_html = soup.prettify()
    
    return cleaned_html


def main():
    """Main function to run the cleaner"""
    import os
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    input_file = os.path.join(script_dir, 'Sample.txt')
    output_file = os.path.join(script_dir, 'cleaned_output.html')
    
    print(f"Cleaning HTML from {input_file}...")
    
    try:
        # Read original file to get its size
        with open(input_file, 'r', encoding='utf-8') as file:
            original_html = file.read()
        original_size = len(original_html)
        
        cleaned_html = clean_html(input_file)
        cleaned_size = len(cleaned_html)
        
        # Calculate reduction
        reduction = original_size - cleaned_size
        reduction_percent = (reduction / original_size * 100) if original_size > 0 else 0
        
        # Save to output file
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(cleaned_html)
        
        print(f"✓ Cleaned HTML saved to {output_file}")
        print(f"✓ Original size: {original_size:,} characters")
        print(f"✓ Cleaned size:  {cleaned_size:,} characters")
        print(f"✓ Reduced by:    {reduction:,} characters ({reduction_percent:.1f}%)")
        
    except FileNotFoundError:
        print(f"Error: Could not find {input_file}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()