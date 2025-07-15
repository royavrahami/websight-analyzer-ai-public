# 📁 מפת מיקומי הנתונים - Microsoft MCP Integration

## 🗂️ **איפה הנתונים מתאכלסים:**

### **📍 המיקום הראשי:**
```
./project_root/
```

---

## 📊 **קבצי נתונים שנוצרו מההרצות:**

### **🎯 קבצי Accessibility Snapshots (JSON):**
```
📄 demo_accessibility_snapshot.json                    (991 bytes)
   └── נתוני הדמו הבסיסי על example.com

📄 real_site_snapshot_www.google.com.json             (13.2 KB)
   └── נתוני Google - 28 אלמנטים אינטראקטיביים

📄 real_site_snapshot_github.com.json                 (85.6 KB)
   └── נתוני GitHub - 167 אלמנטים אינטראקטיביים
```

### **📝 קבצי לוגים (LOG):**
```
📋 mcp_playwright_2a495d4f-a406-4ecf-99a9-e1197fed3a06.log    (2.1 KB)
   └── לוג של הריצה הראשונה שנכשלה (בלי Chromium)

📋 mcp_playwright_710a9b37-ced9-4819-9d05-fdbe5fff51c9.log    (404 bytes)  
   └── לוג של הדמו המוצלח

📋 mcp_playwright_9878581e-b340-40b9-ae6c-fdcb37fea3ce.log    (407 bytes)
   └── לוג של הריצה על Google

📋 mcp_playwright_9f47e539-65f5-43cd-8871-93308d75c495.log    (403 bytes)
   └── לוג של הריצה על GitHub
```

---

## 🗃️ **מבנה הנתונים בכל קובץ:**

### **📄 קבצי JSON - מה יש בפנים:**

#### **1. Accessibility Snapshot Structure:**
```json
{
  "title": "שם העמוד",
  "url": "כתובת האתר", 
  "timestamp": "זמן הצילום",
  "accessibility_tree": {
    "role": "WebArea",
    "name": "שם העמוד",
    "children": [
      // עץ הנגישות המלא
    ]
  },
  "interactive_elements": [
    {
      "type": "סוג האלמנט (button/input/link/etc)",
      "text": "הטקסט הנראה",
      "role": "תפקיד הנגישות", 
      "ariaLabel": "תווית ARIA",
      "id": "מזהה ייחודי",
      "className": "שמות מחלקות CSS",
      "selector": "בורר CSS מדויק",
      "bounds": {
        "x": "מיקום X במסך",
        "y": "מיקום Y במסך", 
        "width": "רוחב האלמנט",
        "height": "גובה האלמנט"
      }
    }
  ],
  "element_count": "סה\"כ אלמנטים"
}
```

#### **2. דוגמה אמיתית - אלמנט מ-GitHub:**
```json
{
  "type": "button",
  "text": "Sign up for GitHub",
  "role": "button", 
  "ariaLabel": "",
  "id": "",
  "className": "btn-mktg",
  "selector": "button:nth-of-type(5)",
  "bounds": {
    "x": 642,
    "y": 325,
    "width": 156,
    "height": 44
  }
}
```

### **📋 קבצי LOG - מה יש בפנים:**
```
2025-06-21 12:20:01,915 - root - INFO - MCP Playwright context initialized with chromium
2025-06-21 12:20:01,917 - root - INFO - MCP Playwright Server started successfully
2025-06-21 12:20:05,630 - root - INFO - Navigated to: https://github.com
2025-06-21 12:20:06,583 - root - INFO - MCP Playwright context closed successfully
2025-06-21 12:20:06,585 - root - INFO - MCP Playwright Server stopped
```

---

## 🔍 **איך לגשת לנתונים:**

### **📂 פתיחת קבצי JSON:**
```bash
# בעורך טקסט
notepad demo_accessibility_snapshot.json

# בדפדפן (לתצוגה יפה) 
start chrome real_site_snapshot_github.com.json

# ב-VS Code
code real_site_snapshot_www.google.com.json
```

### **📋 קריאת לוגים:**
```bash
# הלוג האחרון
type mcp_playwright_9f47e539-65f5-43cd-8871-93308d75c495.log

# כל הלוגים
Get-Content *.log
```

### **📊 ניתוח הנתונים ב-Python:**
```python
import json

# טען נתוני GitHub
with open('real_site_snapshot_github.com.json', 'r', encoding='utf-8') as f:
    github_data = json.load(f)

print(f"כותרת: {github_data['title']}")
print(f"אלמנטים: {github_data['element_count']}")

# מצא כפתורי הרשמה
signup_buttons = [
    el for el in github_data['interactive_elements'] 
    if 'Sign up' in el.get('text', '')
]
print(f"כפתורי הרשמה: {len(signup_buttons)}")
```

---

## 🎯 **איפה מתווספים נתונים חדשים:**

### **🚀 כל הרצה חדשה יוצרת:**

1. **קובץ JSON חדש** עם המבנה:
   ```
   real_site_snapshot_[DOMAIN].json
   ```

2. **קובץ לוג חדש** עם GUID ייחודי:
   ```
   mcp_playwright_[GUID].log  
   ```

3. **המיקום תמיד**: 
   ```
   התיקייה הראשית של הפרויקט
   ```

### **📁 דוגמה לריצה על אתר חדש:**
```bash
# ריצה על stackoverflow.com תיצור:
real_site_snapshot_stackoverflow.com.json
mcp_playwright_[new-guid].log
```

---

## 🛠️ **כלים לניהול הנתונים:**

### **🧹 ניקוי קבצים ישנים:**
```bash
# מחיקת לוגים ישנים (שמור רק את החדשים)
Get-ChildItem "mcp_playwright_*.log" | Sort-Object LastWriteTime | Select-Object -SkipLast 3 | Remove-Item

# מחיקת snapshots של דוגמאות
Remove-Item "demo_accessibility_snapshot.json"
```

### **📊 סיכום הנתונים:**
```bash
# כמה קבצי נתונים יש
(Get-ChildItem "real_site_snapshot_*.json").Count

# גודל כולל של הנתונים
(Get-ChildItem "*.json" | Measure-Object -Property Length -Sum).Sum / 1KB
```

### **🔍 חיפוש בנתונים:**
```bash
# חפש אתרים שנותחו
Get-ChildItem "real_site_snapshot_*.json" | ForEach-Object { $_.Name.Replace("real_site_snapshot_", "").Replace(".json", "") }

# מצא אלמנטים ספציפיים
Select-String "Sign up" real_site_snapshot_github.com.json
```

---

## 📈 **סטטיסטיקות הנתונים הנוכחיים:**

```
📊 סה"כ קבצי נתונים: 3 קבצי JSON
📋 סה"כ קבצי לוג: 4 קבצי LOG
💾 נפח כולל: ~100 KB
🎯 אלמנטים שנותחו: 196 (1+28+167)
🌐 אתרים שנבדקו: 3 (example.com, google.com, github.com)
⏱️ זמן ניתוח כולל: ~12 שניות
```

---

## 🎯 **השלבים הבאים:**

### **💡 רעיונות לשימוש בנתונים:**

1. **יצירת דוחות השוואתיים** בין אתרים
2. **בניית בסיס נתונים** של אלמנטים נפוצים  
3. **יצירת בדיקות אוטומטיות** מהנתונים
4. **ניתוח נגישות מתקדם** לכל אתר
5. **אינטגרציה עם כלי CI/CD** לבדיקות רציפות

### **🚀 תיקיות עתידיות שעשויות להיווצר:**
```
📁 reports/          # דוחות HTML יפים
📁 screenshots/      # צילומי מסך (אם נוסיף)
📁 test_results/     # תוצאות בדיקות שנוצרו
📁 comparisons/      # השוואות בין גרסאות
📁 archives/         # גיבוי נתונים ישנים
```

**🏆 המסקנה: כל הנתונים נמצאים בתיקיית הפרויקט, מאורגנים בקבצים ברורים וניתנים לעיבוד נוח!** 