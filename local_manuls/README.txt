LOCAL MANUL STORAGE - How to Add Your Own Manul Photos
========================================================

This folder is used as a fallback when web scraping fails, or if you want to use your own manul photos.

HOW TO ADD MANULS:

1. Add your manul photos to this folder (JPG, PNG, etc.)
   Example: manul1.jpg, manul2.jpg

2. Edit metadata.json to include information about each photo:

   [
     {
       "name": "Fluffy",
       "location": "Mongolia",
       "description": "A very fluffy manul with beautiful markings",
       "image_file": "manul1.jpg"
     },
     {
       "name": "Grumpy",
       "location": "Altai Mountains",
       "description": "This manul has a permanently grumpy expression",
       "image_file": "manul2.jpg"
     }
   ]

3. The system will randomly select from these manuls when:
   - Web scraping fails
   - Internet is unavailable
   - manulization.com is unreachable

WHERE TO FIND MANUL PHOTOS:
- https://manulization.com/manuls/
- Wikimedia Commons (search "Pallas's cat" or "Otocolobus manul")
- Wildlife photography sites (check licenses!)

NOTE: Make sure you have rights to use any photos you add.
