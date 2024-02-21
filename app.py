import os
import base64
from flask import Flask, flash, jsonify, redirect, render_template, request,url_for,stream_with_context,render_template_string
from tempfile import mkdtemp
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
import mysql.connector
from PIL import Image
import time
from datetime import datetime
# Configure application
app = Flask(__name__)

class dbHelper:
    db_server_address = os.environ.get("DB_SERVER_ADDRESS")
    db_username = os.environ.get("DB_USERNAME")
    db_password = os.environ.get("DB_PASSWORD")
    

    def __init__(self):
        print("starting db connection...")

    def query_exact(self,sql1):
        db = mysql.connector.connect(user=self.db_username, password=self.db_password,
                            host=self.db_server_address,
                            database='recipes')
        #print(sql1)
        cursor=db.cursor()
        cursor.execute(sql1)

        data=cursor.fetchall()
        db.close()
        #print(data)
        if (len2(data) > 0):
            return data[0][0]
        else:
            return 0
        
    def query(self,sql1):
        db = mysql.connector.connect(user=self.db_username, password=self.db_password,
                            host=self.db_server_address,
                            database='recipes')
        cursor=db.cursor()    
        #print(sql1)  
        cursor.execute(sql1)
        data=cursor.fetchall()
        #print(data)
        db.close()
        if (len2(data) > 0):
            return data
        else:
            return 0
        
        
    def insert(self,sql1,image = None):
        db = mysql.connector.connect(user=self.db_username, password=self.db_password,
                            host=self.db_server_address,
                            database='recipes')
        cursor=db.cursor()
        #print(sql1)
        if image == None:
            cursor.execute(sql1)
        else:
            cursor.execute(sql1,image)
        db.commit()
        db.close()

dbhelper = dbHelper()
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

class UploadForm(FlaskForm):
    image = FileField('Image', validators=[FileRequired(), FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/", methods=["GET", "POST"])
def index():
       (week,year) = get_weeknumber()
       return render_template("index.html",week=week,year=year)

@app.route("/weekplan/<week><year>", methods=["GET", "POST"])
def weekplan(week,year,recipeid=None):
       weekplan = WeekPlan(week,year)
       #for i in weekplan.ingredients:
           #print(i.ingredient_image)
       return render_template("weekplan.html",recipes=weekplan.recipes,ingredients = weekplan.ingredients,week=week,year=year)

@app.route("/addrecipe", methods=["GET", "POST"])
def addrecipe():
       if request.method == "POST":
            image = None
            uploaded_file = request.files['file']
            if uploaded_file.filename != '':
                image = uploaded_file.read()
            recipe = Recipe(None,request.form.get("recipename"),request.form.get("content"),image,True)
            return redirect(url_for("ingredients", recipeid=recipe.get_id()))
            # You can save the image to the server or process it as needed

       return render_template("addrecipe.html")

@app.route("/addingredient/<recipeid>", methods=["GET", "POST"])
def ingredients(recipeid):
       recipe = Recipe(recipeid)
       ingredients = get_ingredients()
       form = UploadForm()
       if request.method == "POST":
            newingredient = request.form.get("ingredient")
            newamount = request.form.get("amount")
            newunit = request.form.get("unit")
            ingredient = request.form.get("ingredients")
            image = None
            try:
                uploaded_file = request.files['file']
            except:
                uploaded_file = None
            try:
                if uploaded_file.filename != '':
                    image = uploaded_file.read()
            except:
                image = None
            if newingredient != None:
                ingredient = Ingredient(recipeid,None,newingredient,image,newamount,newunit,True,True)
            else:
                ingredient = Ingredient(recipeid,ingredient,None,None,newamount,newunit,False,True) 
            recipe.add_ingredient(ingredient)  
       return render_template("ingredients.html",recipe=recipe,ingredients=ingredients)

@app.route("/addnutrition/<recipeid>", methods=["GET", "POST"])
def nutrition(recipeid):
       recipe = Recipe(recipeid)
       if request.method == "POST":
            nutrition = Nutrition(recipeid,request.form.get("calories"), request.form.get("sugar"),request.form.get("fat"))
            recipe.set_nutrition(nutrition)
       return render_template("nutrition.html",recipe=recipe)

@app.route("/steps/<recipeid><step>", methods=["GET", "POST"])
def steps(recipeid,step):
       recipe = Recipe(recipeid)
       image = None
       if request.method == "POST":
            updatestepnum =  request.form["add"] 
            uploaded_file = request.files['file']
            try:
                if uploaded_file.filename != '':
                    image = uploaded_file.read()
            except:
                image = None
            recipe.add_step(Step(updatestepnum,request.form.get("content"),image))
       currentstep = recipe.get_step(step)
       recipe = Recipe(recipeid)
       return render_template("steps.html",recipe=recipe,currentstep=currentstep,step=step)

@app.route("/viewrecipes", methods=["GET", "POST"])
def viewrecipes():
    ingredients = get_ingredients()
    if request.method == "POST":
       try:
            ingredients = request.form.get("ingredients")
       except ValueError:
             ingredients = 0
             print(ValueError)
       recipes = get_all_recipe(ingredients)
       ingredients = get_ingredients()
       return render_template("viewrecipes.html",ingredients=ingredients)
    else:
       return render_template("viewrecipes.html")

@app.route("/streamrecipes")
def streamrecipes():
    @stream_with_context
    def generate():


   #   <button type="submit" name="addweekrecipe" value="{{n.recipe_id}}">Add Recipe for this Week</button>
   #   <button type="submit" name="addnextweekrecipe" value="{{n.recipe_id}}">Add Recipe for Next Week</button>
      
   # </div>  
        recipes = []
        sql1="select recipe_id from recipe"
        data = dbhelper.query(sql1)
        yield render_template_string('<form class="form-inline" method="post" action="/recipesteps" target="_parent" id = "recipesteps">\n')
        yield render_template_string('<div class="container">\n')
        yield render_template_string('<div class="row">\n')
        
        if (len2(data) > 0):
            for i in data:
                recipe = Recipe(i[0],None,None,None)
                yield render_template_string('<div class = "col-sm">\n')
                yield render_template_string("<p>{{recipe_name}}</p>",recipe_name = recipe.recipe_name)
                yield render_template_string("</div>")
                yield render_template_string('<div class = "col-sm">\n')
                yield render_template_string('<button type="submit" name="recipeid" value="{{recipe_id}}"  > <img class="img-fluid" src="{{ url_for("static", filename=display_image) }}" alt="{{recipe_name}}"></button>',recipe_id=recipe.recipe_id,display_image=recipe.display_image,recipe_name=recipe.recipe_name)
                yield render_template_string("</div>")
                yield render_template_string('<div class = "col-sm">\n')
                yield render_template_string('<button type="submit" name="addweekrecipe" value="{{recipe_id}}">Add Recipe for this Week</button>',recipe_id=recipe.recipe_id)
                yield render_template_string(' <button type="submit" name="addnextweekrecipe" value="{{recipe_id}}">Add Recipe for Next Week</button>',recipe_id=recipe.recipe_id)
        yield render_template_string('</div>\n')
        yield render_template_string('</div>\n')
        yield render_template_string('</form>\n')
    return app.response_class(generate())

@app.route("/recipesteps", methods=["POST"])
def recipesteps():
    (week,year) = get_weeknumber()
    if request.method == "POST":
        thisweek = request.form.get("addweekrecipe")
        nextweek = request.form.get("addnextweekrecipe")
        recipe = Recipe(request.form.get("recipeid"))
        if (thisweek != None):
            weekplan = WeekPlan(week,year)
            weekplan.add_recipe(thisweek)
        if (nextweek != None):
            weekplan = WeekPlan(int(week) + 1,year)
            weekplan.add_recipe(int(nextweek))
    return render_template("recipesteps.html",recipe = recipe)

@app.route("/recipelist", methods=["POST"])
def recipelist():
    (week,year) = get_weeknumber()
    if request.method == "POST":
        thisweek = request.form.get("addweekrecipe")
        nextweek = request.form.get("addnextweekrecipe")
        ingredients = request.form.getlist("ingredients")
        if len2(ingredients) == 0:
            ingredients=None
        recipes = get_all_recipe(ingredients)
        if (thisweek != None):
            weekplan = WeekPlan(week,year)
            weekplan.add_recipe(thisweek)
        if (nextweek != None):
            weekplan = WeekPlan(int(week) + 1,year)
            weekplan.add_recipe(int(nextweek))
        recipes = get_all_recipe()
        return render_template("recipelist.html",recipes=recipes,week=week,year=year)
    else:
        recipes = get_all_recipe()
    return render_template("recipelist.html",recipes = recipes,week=week)

@app.route("/editingredients", methods=["GET", "POST"])
def editingredients():
    ingredients = get_ingredients()
    ingredientlist = []
    image = None
    if request.method == "POST":
        id = request.form["fileimage"]
        try:
            uploaded_file = request.files['file']
        except:
            uploaded_file = None
        try:
            if uploaded_file.filename != '':
                image = uploaded_file.read()
        except:
            image = None
        name = request.form.get("name")
        Ingredient(None,id,name,image,None,None,True)
        ingredients = get_ingredients()

    return render_template("ingredientlist.html",ingredients = ingredients)

@app.route("/recipelistcontains", methods=["POST"])
def recipelistcontains():
    (week,year) = get_weeknumber()
    recipes = None
    if request.method == "POST":
        recipes = get_all_recipe(request.form.get("ingredients"))
    return render_template("recipelist.html",recipes = recipes,week=week)

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return render_template("apology.html")

def get_all_recipe_from_ingredients(ingredients):

   text = ''
   for i in range(0,len2(ingredients)):
       text = text +  " il.ingredient_id = '"+ str(ingredients[i]) + "'"
       if i < len2(ingredients) -1:
           text = text + " or "
   sql1="select r.recipe_id, r.recipe_name from ingredientlist il inner join recipe r on r.recipe_id = il.recipe_id where " + text
   data=dbhelper.query(sql1)
   #print(data)
   if (len2(data) > 0):
      return data
   else:
      return ()
   
def get_all_recipe_contains_ingredients(ingredients):
   text = ''
   for i in range(0,len2(ingredients)):
       text = text + "'" + str(ingredients[i]) + "'"
       if i < len2(ingredients) -1:
           text = text + ", "
   sql1="SELECT il.recipe_id, r.recipe_name FROM ingredientlist il JOIN ingredient i ON il.ingredient_id = i.ingredient_id inner join recipe r on r.recipe_id = il.recipe_id WHERE i.ingredient_id IN (" + text + ") GROUP BY il.recipe_id HAVING COUNT(DISTINCT i.ingredient_id) = " + str(len2(ingredients))
   #print(sql1)
   data=dbhelper.query(sql1)
   #print(data)
   if (len2(data) > 0):
      return data
   else:
      return ()

# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

def get_all_recipe(ingredient=None):
    recipes = []
    if ingredient != None:
        sql1="select recipe_id from ingredientlist where ingredient_id = " + str(ingredient)
        data = dbhelper.query(sql1)        
        if (len2(data) > 0):
            for i in data:
                recipe = Recipe(i[0],None,None,None)
                recipes.append(recipe)
    else:
        sql1="select recipe_id from recipe"
        data = dbhelper.query(sql1)
        if (len2(data) > 0):
            for i in data:
                recipe = Recipe(i[0],None,None,None)
                recipes.append(recipe)
     
    return recipes

def get_ingredients():
    sql1="select ingredient_id from ingredient order by ingredient"
    data = dbhelper.query(sql1)
    ingredients = []
    for i in data:
        ingredients.append(Ingredient(None,i[0],None,None,None,None))
    return ingredients

def get_weeknumber():
    currentYear = datetime.now().year
    year = currentYear - 2023
    week_number = int(datetime.now().strftime('%U')) + 1
    return(week_number,year)

def save_image(image_path,imagedata):
    # Check if the 'images' folder exists, if not, create it

    # Open the image file
    with open(image_path, 'wb') as file:
        file.write(imagedata)
        # Save the image in the 'images' folder
        print(f"Image saved successfully at {image_path}")

def get_image(image_path):
    try:
        with open(image_path, 'rb') as file:
            encoded_image = base64.b64encode(file.read()).decode()
            #print(encoded_image)
            return encoded_image
    except:
        return 0

def len2(item):
    if isinstance(item, int):
        return 0
    else:
        return len(item)

class Ingredient:
        ingredient_id = 0
        ingredient = ""
        imagedata = None
        ingredient_image = None
        display_image = None
        amount = 0
        unit = ""
        recipe_id = 0
        ingredientlist_id = 0
        

        def __init__(self,recipe_id=None,ingredient_id=None,ingredient=None,image=None,newamount=None,newunit=None,update=False,newingredient=False):
            if ingredient_id != None:
                self.ingredient_id = ingredient_id
                self.get_ingredient()
            if ( ingredient != None):
                self.ingredient = ingredient
            if (image != None):
                self.imagedata = image
            if update == True:    
                self.add_ingredient()
            if (recipe_id != None and newamount != None and newunit != None):
                self.amount = newamount
                self.unit = newunit
                self.recipe_id = recipe_id
                if newingredient == True:
                    self.add_recipe_ingredient()
            if self.ingredient_image != None:
                self.display_image = self.ingredient_image


        def get_ingredient(self):
            if self.ingredient_id != 0:
                sql1 = "select ingredient,ingredient_id from ingredient where ingredient_id = " + str(self.ingredient_id)
                data = dbhelper.query(sql1)
                if len2(data) != 0:
                    self.ingredient = data[0][0]
                    self.ingredient_id = data[0][1]
                    new_path = os.path.join("images", 'ingredient')
                    new_path = os.path.join(new_path,str(data[0][1]) + ".jpg")
                    image = new_path
                    if image != 0 and image != None:
                        self.ingredient_image = image
                        self.display_image = image

            else:
                self.add_ingredient()

        def add_ingredient(self):
            if self.ingredient != "":
                sql1="select ingredient_id from ingredient where ingredient = '" + str(self.ingredient) + "'"
                data = dbhelper.query_exact(sql1)
                if data != 0:
                    self.ingredient_id = data
            if self.ingredient_id != 0:        
                if self.imagedata != None:
                    sql1= "update ingredient set image = %s where ingredient_id = " + str(self.ingredient_id)
                    dbhelper.insert(sql1,(self.imagedata,))
                    sql1="select ingredient_id from ingredient where ingredient = '" + str(self.ingredient) + "'"
                    data = dbhelper.query_exact(sql1)
                    if data != 0:
                        self.ingredient_id = data
                    else:
                        self.ingredient_id = 0
                    filename = os.path.basename("static")
                    new_path = os.path.join(filename,"images")
                    new_path = os.path.join(new_path, 'ingredient')
                    new_path = os.path.join(new_path,str(self.ingredient_id) + ".jpg")
                    self.display_image = new_path
                    self.ingredient_image = new_path
                    save_image(new_path,self.imagedata)
            else:       
                if self.imagedata != None:
                    sql1= "insert into ingredient (ingredient,image) values (" + '"' + str(self.ingredient) + '"' +", %s)"
                    dbhelper.insert(sql1,(self.imagedata,))
                    sql1="select ingredient_id from ingredient where ingredient = '" + str(self.ingredient) + "'"
                    data = dbhelper.query_exact(sql1)
                    if data != 0:
                        self.ingredient_id = data
                    else:
                        self.ingredient_id = 0
                    filename = os.path.basename("static")
                    new_path = os.path.join(filename,"images")
                    new_path = os.path.join(new_path, 'ingredient')
                    new_path = os.path.join(new_path,str(self.ingredient_id) + ".jpg")
                    self.display_image = new_path
                    self.ingredient_image = new_path
                    save_image(new_path,self.imagedata)
                else:
                    sql1= "insert into ingredient (ingredient) values (" + '"' + str(self.ingredient) + '"' + ")"
                    dbhelper.insert(sql1)
            sql1="select ingredient_id from ingredient where ingredient = '" + str(self.ingredient) + "'"
            data = dbhelper.query_exact(sql1)
            if data != 0:
                self.ingredient_id = data
            else:
                self.ingredient_id = 0
                
        def get_recipe_ingredient(self):
                sql1="select ingredientlist_id,amount,unit from ingredientlist where recipe_id = " + str(self.recipe_id) + " and ingredient_id = " + str(self.ingredient_id)
                data = dbhelper.query(sql1)
                if (len2(data) > 0):
                    self.ingredientlist_id = data[0][0]
                    if (self.amount == None and self.unit == None):
                        self.amount = data[0][1]
                        self.unit = data[0][2]

        def add_recipe_ingredient(self):
                self.get_recipe_ingredient()
                if (self.ingredientlist_id != 0):
                    sql1 = "update ingredientlist set amount = " + str(self.amount) + ",unit = " + '"' + str(self.unit) + '"' + " where ingredientlist_id = " + str(self.ingredientlist_id)
                else:
                    sql1= "insert into ingredientlist (recipe_id,ingredient_id,amount,unit) values (" + str(self.recipe_id) + "," + str(self.ingredient_id) + "," + '"' + str(self.amount)  + '"' + "," + '"' + str(self.unit) + '"' + ")"
                dbhelper.insert(sql1)
                self.get_recipe_ingredient()

class Nutrition:
        calories = 0
        fat = 0
        sugar = 0
        nutrition_id = 0

        def __init__(self,id,calories=None,sugar=None,fat=None):
            if (id != None and ( calories == None or fat == None or sugar == None)):
                sql1="select nutrition_id,calories,sugar,fat from nutrition where recipe_id ='" + str(id) +"'" 
                data = dbhelper.query(sql1)
                #print(str(recipe_id))

                if (len2(data) > 0):
                    self.nutrition_id = data[0][0]
                    self.calories = data[0][1]
                    self.sugar = data[0][2]
                    self.fat = data[0][3]
            else:
                self.calories = calories
                self.fat = fat
                self.sugar = sugar

        def copy(self,nutrition):
            self.calories = nutrition.calories
            self.fat = nutrition.fat
            self.sugar = nutrition.sugar
            self.nutrition_id = nutrition.nutrition_id

class Step:
        step_num = 0
        instruction = ""
        step_image = None
        display_image = None

        def __init__(self,step_num,instruction,step_image):
            self.step_image = step_image
            self.step_num = step_num
            self.instruction = instruction
            if self.step_image != None:
                self.display_image = self.step_image

class Recipe:
        recipe_name = ""
        recipe_id = 0
        description = ""
        recipe_image = None
        display_image = None
        ingredients = []
        nutrition = None
        steps = []
        maxstep = 0
        
        ## Initializers ##
         
        def __init__(self,id,name=None,description=None,image= None,update = False):
            self.ingredients = []
            self.nutrition = None
            self.recipe_image = None
            self.recipe_id = 0
            self.recipe_name = ""
            self.steps = []
            if id != None and name == None and description == None and image == None:
                self.recipe_id = id
                self.get_recipe()
            else:
                self.recipe_name = name
                self.description = description
                self.recipe_image = image
                if update:
                    self.add_recipe()
            self.get_steps()
            self.get_ingredients()
            self.get_nutrition()
        ### Setters
        
        def set_nutrition(self,nutrition):
            self.nutrition = nutrition
            self.add_nutrition()
       
        def set_name(self,name):
            self.recipe_name = name

        def set_id(self,id):
            self.recipe_id = id

        def set_image(self,image):
            self.recipe_image = image
        
        def set_step(self,step):
            if (self.get_step(step.step_num) == None):
                self.steps.append(step)
                if step.step_num > self.maxstep:
                    self.maxstep = step.step_num

        def set_description(self,description):
            self.description = description
        
        ### Getters
        
        def get_name(self):
            return self.recipe_name
        
        def get_id(self):
            return self.recipe_id
        
        def get_image(self):
            return self.recipe_image
        
        def get_description(self):
            return self.description
        
        def get_recipe(self):
            sql1="select recipe_name, description from recipe where recipe_id = '" + str(self.recipe_id) + "'"
            data = dbhelper.query(sql1)
            if data != 0:
                self.recipe_name = data[0][0]
                self.description = data[0][1]
            self.recipe_image = "images/recipe/" + str(self.recipe_id) + ".jpg"
            self.display_image = self.recipe_image

        def get_ingredients(self):
            if self.recipe_id != 0:
                sql1="select i.ingredient_id,i.ingredient,il.amount,il.unit from ingredient i inner join ingredientlist il on i.ingredient_id = il.ingredient_id where recipe_id ='" + str(self.recipe_id) +"' order by i.ingredient desc" 
                data = dbhelper.query(sql1)
                if len2(data) != 0:
                    for i in data:
                        ingredient = None
                        ingredient = Ingredient(self.recipe_id,i[0],i[1],None,i[2],i[3])
                        self.add_ingredient(ingredient)

        def get_nutrition(self):
            nutrition = Nutrition(self.recipe_id)
            if (nutrition.nutrition_id > 0):
                self.nutrition = nutrition

        def get_steps(self):
            self.steps = []
            sql1 = "select step,instruction from recipestep where recipe_id = " + str(self.recipe_id)
            data = dbhelper.query(sql1)

            if len2(data) != 0:
                for i in data:
                    new_path = os.path.join("images", 'steps')
                    new_path = os.path.join(new_path, str(self.recipe_id) + "-" + str(i[0]) + ".jpg" )
                    image = new_path
                    step = Step(i[0],i[1],image)
                    self.set_step(step)

        def get_step(self,stepnum):
            for i in self.steps:
                if str(i.step_num) == str(stepnum):
                    return i
            return None
        
        ## Adders ##

        def add_recipe(self):
            sql1="select recipe_id from recipe where recipe_name = '" + str(self.recipe_name) + "'"
            data = dbhelper.query_exact(sql1)
            if (data > 0):
                self.recipe_id = data
                sql1 = "update recipe set recipe_name = "+ '"' + self.recipe_name + '"' + ", description = " + '"' + self.description + '"' + " where recipe_id = " + self(self.recipe_id)
            else:
                sql1= "insert into recipe (recipe_name,description) values ("+'"' + str(self.recipe_name) + '"' +","+ '"' + str(self.description) + '"' + ")"
            dbhelper.insert(sql1)
            sql1="select recipe_id from recipe where recipe_name = '" + str(self.recipe_name) + "'"
            self.recipe_id = dbhelper.query_exact(sql1)
            self.add_recipe_image()

        def add_recipe_image(self):
            if self.recipe_id != 0 and self.recipe_image != None:
                filename = os.path.basename("static")
                new_path = os.path.join(filename,"images")
                new_path = os.path.join(new_path,"recipe")
                new_path = os.path.join(new_path,str(self.recipe_id) + ".jpg")
                save_image(new_path,self.recipe_image)

        def add_ingredient(self,ingredient):
            if ingredient not in self.ingredients:
                self.ingredients.append(ingredient)       

        def add_nutrition(self):
            sql1 = "select nutrition_id from nutrition where recipe_id = " + str(self.recipe_id)
            data = dbhelper.query_exact(sql1)
            if len2(data) != 0:
                sql1 = "update nutrition set  calories = " + str(self.nutrition.calories) +",fat = " + str(self.nutrition.fat) + ",sugar = " + str(self.nutrition.sugar) + " where nutrition_id =  " + str(data)
            else:
                sql1 = "insert into nutrition (fat,calories,sugar,recipe_id) values (" +str(self.nutrition.fat) + "," +str(self.nutrition.calories) + "," +str(self.nutrition.sugar) + "," + str(self.recipe_id) + ")"
            dbhelper.insert(sql1)

        def add_step(self,step):
            filename = os.path.basename("static")
            new_path = os.path.join(filename,"images")
            new_path = os.path.join(new_path, 'steps')
            new_path = os.path.join(new_path, str(self.recipe_id) + "-" + str(step.step_num) + ".jpg" )
            if step.step_image != 0 and step.step_image != None:
                save_image(new_path,step.step_image)
            sql1 = "select recipestep_id from recipestep where step = " + str(step.step_num) + " and recipe_id = " + str(self.recipe_id)
            data = dbhelper.query_exact(sql1)
            
            if len2(data) != 0:
                sql1 = "update recipestep set instruction = " + '"' + str(step.instruction) + '"' + " where recipestep_id = " + str(data)
                dbhelper.insert(sql1)
            else:
                sql1 = "insert into recipestep (recipe_id,step,instruction) values ("+ str(self.recipe_id) + ","  +str(step.step_num) + ',"' + str(step.instruction) + '"' + ")"
                dbhelper.insert(sql1)

        ## checks ##
                    
        def check_ingredient(self,ingredient):
            for i in self.ingredients:
                if (str(i.ingredient_id) == str(ingredient)):
                    return True
            return False

class WeekPlan:
    week = 0
    year = 0
    recipes = []
    ingredients = []


    def __init__(self,week,year):
        self.ingredients = []
        self.recipes = []
        self.week = week
        self.year = year
        self.get_weekplan()
        self.get_ingredients()


    def get_weekplan(self):
        sql1 = "select recipe_id from weekplan where week = " + str(self.week) + " and year = " + str(self.year)
        #print(sql1)
        data = dbhelper.query(sql1)
        if len2(data) != 0:
            for i in data:
                self.recipes.append(Recipe(i[0]))
    
    def add_recipe(self,recipe_id):
        sql1 = "select weekplan_id from weekplan where week = " +str(self.week) + " and year = " + str(self.year) + " and recipe_id = " + str(recipe_id) 
        data = dbhelper.query_exact(sql1)
        if len2(data) == 0:
            sql1 = "insert into weekplan (week,year,recipe_id) values (" + str(self.week) + "," + str(self.year) + "," + str(recipe_id) + ")"
            dbhelper.insert(sql1)
        found = False
        for i in self.recipes:
            if i.recipe_id == recipe_id:
                found = True
        if not found:
            self.recipes.append(Recipe(recipe_id))

    def get_ingredients(self):
        for i in self.recipes:
            for j in i.ingredients:
                if len2(self.ingredients) != 0:
                    found = False
                    for k in self.ingredients:
                        if int(j.ingredient_id) == int(k.ingredient_id):
                            found = True
                            k.amount = float(k.amount) + float(j.amount)
                    if (not found):
                        self.ingredients.append(j)

                else:
                    self.ingredients.append(j)



if __name__ == "__main__":
    app.run(host='0.0.0.0')
    
    