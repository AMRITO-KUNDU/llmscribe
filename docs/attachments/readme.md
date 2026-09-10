# Wallpaper CDN

A lightweight wallpaper CDN powered by GitHub.

Drop images into folders → push → get a ready-to-use JSON index.  
No backend. No database. No setup. Just plug and play.

## ✨ Features

- 📁 Organized wallpapers by category
- 🖼️ Fast image delivery via jsDelivr CDN
- 📄 Automatically generated `images.json`
- 🔄 Auto-updates whenever wallpapers are added or removed
- 🌐 Works with Android, iOS, Flutter, React Native, Web, Desktop
- 🚀 No backend or database required
- 🆓 Completely free

---

## 🚀 Quick Start

### 1. Fetch the JSON

**Recommended (faster):**
```
https://cdn.jsdelivr.net/gh/AMRITO-KUNDU/wallpapers-CDN@main/images.json
```

**Direct from GitHub:**
```
https://raw.githubusercontent.com/AMRITO-KUNDU/wallpapers-CDN/main/images.json
```

### 2. Use it in your app

```js
// JavaScript / Web
fetch("https://cdn.jsdelivr.net/gh/AMRITO-KUNDU/wallpapers-CDN@main/images.json")
  .then(res => res.json())
  .then(data => console.log(data));
```

```dart
// Flutter
final response = await http.get(Uri.parse(
  "https://cdn.jsdelivr.net/gh/AMRITO-KUNDU/wallpapers-CDN@main/images.json"
));
final data = jsonDecode(response.body);
```

```js
// React Native
const response = await fetch(
  "https://cdn.jsdelivr.net/gh/AMRITO-KUNDU/wallpapers-CDN@main/images.json"
);
const data = await response.json();
```

---

## 📂 Repository Structure

```text
.
├── wallpapers/
│   ├── Anime/
│   ├── Abstract/
│   ├── Nature/
│   ├── Quotes/
│   ├── Space/
│   └── ...
├── images.json
└── .github/
    └── workflows/
        └── generate-image-json.yml
```

Each folder inside `wallpapers/` is a category.

---

## 📄 JSON Format

```json
[
  {
    "category": "Nature",
    "files": [
      {
        "name": "nature-mountain-lake.jpg",
        "url": "https://cdn.jsdelivr.net/gh/AMRITO-KUNDU/wallpapers-CDN@main/wallpapers/Nature/nature-mountain-lake.jpg"
      }
    ]
  }
]
```

| Field      | Description              |
|------------|--------------------------|
| `category` | Wallpaper category name  |
| `files`    | List of wallpapers       |
| `name`     | Filename                 |
| `url`      | Direct image URL         |

---

## ⚙️ How It Works

1. You add or remove images inside `wallpapers/`
2. You push to GitHub
3. GitHub Action runs automatically
4. It scans every category and generates a fresh `images.json`
5. The updated JSON is committed back to the repository

Your apps always receive the latest wallpapers.

---

## 🖼️ Supported Image Formats

- JPG / JPEG
- PNG
- WebP

---

## 🤝 Adding New Wallpapers

1. Create a new folder under `wallpapers/` (or use an existing one)
2. Drop your images inside it
3. Commit and push

GitHub Actions will automatically update `images.json`.  
No manual editing required.

---

## 📜 License

MIT

Please only upload wallpapers you have the legal right to distribute.
