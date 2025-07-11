import csv
import os
import re
import shutil

def natural_sort_key(text):
    """
    Convert a string into a list of string and number chunks.
    "car-name-2.jpg" becomes ["car-name-", 2, ".jpg"]
    This allows for proper numerical sorting.
    """
    import re
    def atoi(text):
        return int(text) if text.isdigit() else text
    return [atoi(c) for c in re.split(r'(\d+)', text)]

def rename_files_in_folder(folder_path, folder_name):
    """
    Rename all files in a folder to follow the pattern: folder-name-1.ext, folder-name-2.ext, etc.
    Files are renamed in their natural sort order, but only if needed.
    """
    if not os.path.isdir(folder_path):
        return
    
    # Get all files (excluding hidden files and directories)
    files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f)) and not f.startswith('.')]
    
    if not files:
        return
    
    # Sort files naturally
    files.sort(key=natural_sort_key)
    
    # Prepare expected names
    expected_names = []
    for i, old_name in enumerate(files, 1):
        _, ext = os.path.splitext(old_name)
        expected_names.append(f"{folder_name}-{i}{ext}")
    
    # Only rename if needed
    for old_name, expected_name in zip(files, expected_names):
        if old_name != expected_name:
            old_path = os.path.join(folder_path, old_name)
            new_path = os.path.join(folder_path, expected_name)
            # If the target name already exists, find a temporary name to avoid collision
            if os.path.exists(new_path):
                temp_path = os.path.join(folder_path, f"__temp__{old_name}")
                os.rename(old_path, temp_path)
                old_path = temp_path
            os.rename(old_path, new_path)
            print(f"  Renamed: {old_name} → {expected_name}")

def format_brazilian_phone(phone):
    """
    Format Brazilian phone number from +5511980553559 to (11) 98055-3559
    """
    # Remove +55 and any non-digit characters
    digits = re.sub(r'[^\d]', '', phone)
    
    # If it starts with 55, remove it (Brazil country code)
    if digits.startswith('55'):
        digits = digits[2:]
    
    # Format as (XX) XXXXX-XXXX
    if len(digits) == 11:  # Mobile number
        return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
    elif len(digits) == 10:  # Landline number
        return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
    else:
        return phone  # Return original if format is unexpected

# Read vehicles from CSV
vehicles = []
with open('vehicles.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        vehicles.append(row)

# Rename files in each car's folder to follow consistent naming
print("Renaming files in car folders...")
for v in vehicles:
    folder_name = v['image_folder']
    folder_path = f"img/{folder_name}"
    if os.path.isdir(folder_path):
        print(f"Processing folder: {folder_name}")
        rename_files_in_folder(folder_path, folder_name)
    else:
        print(f"Warning: Folder {folder_path} does not exist")
print("File renaming completed!\n")

# Clean up orphaned HTML files in anuncios folder
print("Cleaning up orphaned HTML files...")
if os.path.exists('anuncios'):
    # Get all HTML files in anuncios folder
    existing_files = [f for f in os.listdir('anuncios') if f.endswith('.html')]
    
    # Get expected filenames from CSV
    expected_files = [f"{v['image_folder']}.html" for v in vehicles]
    
    # Find orphaned files (files that exist but are not in CSV)
    orphaned_files = [f for f in existing_files if f not in expected_files]
    
    # Delete orphaned files
    for orphaned_file in orphaned_files:
        file_path = os.path.join('anuncios', orphaned_file)
        try:
            os.remove(file_path)
            print(f"  Deleted orphaned file: {orphaned_file}")
        except Exception as e:
            print(f"  Error deleting {orphaned_file}: {e}")
    
    if not orphaned_files:
        print("  No orphaned files found")
print("Cleanup completed!\n")

html_start = '''<!DOCTYPE html>
<html lang="pt-br">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Carros à Venda</title>
  <link rel="stylesheet" href="css/style.css">
</head>
<body>
  <header>
    <img src="img/logo.png" alt="Logo">
  </header>
  <main class="grid">
'''

html_end = '''
  </main>
</body>
</html>
'''

cards = ""
for v in vehicles:
    # Check if vehicle should be published (shown on main page)
    publish = v.get("publish", "true").lower() == "true"
    
    # Main image: first image in natural order from the folder
    img_folder = f"img/{v['image_folder']}"
    main_img = "img/placeholder.jpg"  # fallback placeholder
    if os.path.isdir(img_folder):
        imgs = sorted([f for f in os.listdir(img_folder) if not f.startswith('.')], key=natural_sort_key)
        if imgs:
            main_img = f"img/{v['image_folder']}/{imgs[0]}"
    
    # Generate link automatically from image_folder name
    link = f"anuncios/{v['image_folder']}.html"
    
    # Only add card to main page if published
    if publish:
        cards += f'''
        <a href="{link}" class="card">
          <img src="{main_img}" alt="{v["title"]}">
          <div class="info">{v["title"]}</div>
        </a>
        '''

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html_start + cards + html_end)

# Generate detail pages for each vehicle
detail_template = '''<!DOCTYPE html>
<html lang="pt-br">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <link rel="stylesheet" href="../css/style.css">
  <link rel="stylesheet" href="../css/basicLightbox.min.css">
  <style>
    .lightbox-arrow {{ position: fixed; top: 50%; transform: translateY(-50%); font-size: 2.5em; color: #fff; background: rgba(0,0,0,0.3); border: none; z-index: 1100; cursor: pointer; padding: 0 18px; border-radius: 8px; user-select: none; }}
    .lightbox-arrow.left {{ left: 20px; }}
    .lightbox-arrow.right {{ right: 20px; }}
    .lightbox-close {{ position: fixed; top: 24px; left: 24px; font-size: 2.2em; color: #fff; background: rgba(0,0,0,0.3); border: none; z-index: 1200; cursor: pointer; border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; }}
    .lightbox-close:hover {{ background: rgba(0,0,0,0.5); }}
  </style>
</head>
<body>
  <header>
    <a href="../index.html">
      <img src="../img/logo.png" alt="Logo">
    </a>
  </header>
  <main class="car-page">
    <aside class="car-sidebar">
      <img class="car-main-photo" src="../{main_img}" alt="{title}">
      <div class="car-title">{title}</div>
      <a class="whatsapp-btn" href="https://wa.me/{whatsapp_link}" target="_blank">
        <img src="../img/whats-logo.png" alt="WhatsApp" class="whats-icon">{whatsapp_display}
      </a>
      <ul class="car-details">
        <li><strong>Marca:</strong> {make}</li>
        <li><strong>Modelo:</strong> {model}</li>
        <li><strong>Ano:</strong> {year}</li>
        <li><strong>Cor:</strong> {color}</li>
        <li><strong>Quilometragem:</strong> {mileage}</li>
        <li><strong>Potência:</strong> {power}</li>
        <li><strong>Preço:</strong> {price}</li>
        <li><strong>Localização:</strong> {location}</li>
        <li><strong>Descrição:</strong> {description}</li>
      </ul>
    </aside>
    <section class="car-content">
      {gallery}
      <p><a href="../index.html">&larr; Voltar para a listagem</a></p>
    </section>
  </main>
  <script src="../js/basicLightbox.min.js"></script>
  <script>
    document.addEventListener('DOMContentLoaded', function() {{
      var images = Array.from(document.querySelectorAll('.gallery-img'));
      var currentInstance = null;
      var currentIndex = 0;
      
      function showLightbox(idx) {{
        currentIndex = idx;
        var instance = basicLightbox.create(`
          <button class="lightbox-close">&times;</button>
          <button class="lightbox-arrow left">&#8592;</button>
          <img src="${{images[idx].src}}" style="max-width:90vw;max-height:90vh;display:block;margin:auto;">
          <button class="lightbox-arrow right">&#8594;</button>
        `, {{
          onShow: (inst) => {{
            currentInstance = inst;
            var closeBtn = inst.element().querySelector('.lightbox-close');
            var left = inst.element().querySelector('.lightbox-arrow.left');
            var right = inst.element().querySelector('.lightbox-arrow.right');
            var img = inst.element().querySelector('img');
            
            closeBtn.onclick = function(e) {{ e.stopPropagation(); inst.close(); }};
            
            left.onclick = function(e) {{ 
              e.stopPropagation(); 
              currentIndex = (currentIndex - 1 + images.length) % images.length;
              img.src = images[currentIndex].src;
            }};
            
            right.onclick = function(e) {{ 
              e.stopPropagation(); 
              currentIndex = (currentIndex + 1) % images.length;
              img.src = images[currentIndex].src;
            }};
            
            document.onkeydown = function(ev) {{
              if(ev.key === 'ArrowLeft') {{ 
                currentIndex = (currentIndex - 1 + images.length) % images.length;
                img.src = images[currentIndex].src;
              }}
              if(ev.key === 'ArrowRight') {{ 
                currentIndex = (currentIndex + 1) % images.length;
                img.src = images[currentIndex].src;
              }}
              if(ev.key === 'Escape') {{ inst.close(); }}
            }};
          }},
          onClose: () => {{ 
            document.onkeydown = null; 
            currentInstance = null;
          }}
        }});
        instance.show();
      }}
      
      images.forEach(function(img, i) {{
        img.setAttribute('data-index', i);
        img.addEventListener('click', function() {{ showLightbox(i); }});
      }});
    }});
  </script>
</body>
</html>
'''

os.makedirs('anuncios', exist_ok=True)
for v in vehicles:
    img_folder = f"img/{v['image_folder']}"
    gallery = ""
    main_img = "img/placeholder.jpg"  # fallback placeholder
    gallery_imgs = []
    if os.path.isdir(img_folder):
        imgs = sorted([f for f in os.listdir(img_folder) if not f.startswith('.')], key=natural_sort_key)
        if imgs:
            main_img = f"img/{v['image_folder']}/{imgs[0]}"
            gallery_imgs = [f"img/{v['image_folder']}/{img}" for img in imgs]
    # Gallery HTML
    if gallery_imgs:
        gallery += '<div class="car-gallery">'
        for idx, img in enumerate(gallery_imgs):
            gallery += f'<img src="../{img}" class="gallery-img" loading="lazy" data-index="{idx}">'  # add data-index
        gallery += '</div>'
    # Format WhatsApp number for display and link
    whatsapp_raw = v.get("whatsapp", "")
    whatsapp_display = format_brazilian_phone(whatsapp_raw)
    whatsapp_link = re.sub(r'[^\d]', '', whatsapp_raw)  # Remove all non-digits for the link
    
    detail_html = detail_template.format(
        title=v["title"],
        main_img=main_img,
        price=v.get("price", ""),
        location=v.get("location", ""),
        description=v.get("description", ""),
        whatsapp_link=whatsapp_link,
        whatsapp_display=whatsapp_display,
        make=v.get("make", "-"),
        model=v.get("model", "-"),
        year=v.get("year", "-"),
        color=v.get("color", "-"),
        mileage=v.get("mileage", "-"),
        power=v.get("power", "-"),
        gallery=gallery
    )
    # Generate filename from image_folder name
    filename = f"{v['image_folder']}.html"
    with open(f'anuncios/{filename}', 'w', encoding='utf-8') as f:
        f.write(detail_html)

print("index.html and detail pages generated!") 