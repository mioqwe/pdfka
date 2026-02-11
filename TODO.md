## Aplication that should create branding pdf files/presentations from json

### todo:

1. initial json file with structure

structure like: 

```json
{
  "1": {
    "header": "Brand name",
    "content": "jinja2 html template without styling"
  },
  "2": {
    "header": "We offer you something",
    "content": "jinja2 html template without styling"
  }
}
```

so basicaly 1,2 its pdf pages, and content its content on this pages. 

2. the program should take arguments about company via cli...  

Like main.py cp_name="Imperial Medica" cp_rating=4.0 cp_reviews=123
All the variables should be like not neccessery, but they should work if there are here! 
All manages with jinja2 template engine
**maybe** also program should take initial json... with mesurements and images on each page.

3. Input to program should be json... with structure that i`ve provided above. 
4. At the end program should generate pdf file... and return file path and name.
 
## Problems
- what if content of the page would be larger then page ? how to structure data on the page...

Maybe we should have like initial, pdf stracture... and mesure how much words each page can suit.
So like we have page #1: 
This page has:
- image, header, footer, and some space for text...

So then we would just change text... and thats it... 


