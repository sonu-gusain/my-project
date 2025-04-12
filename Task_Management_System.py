
import mysql.connector
from fastapi import FastAPI , Depends , HTTPException 
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel , EmailStr
from typing import List , Optional
from jose import jwt , JWTError
from datetime import datetime , timedelta , date
from passlib.context import CryptContext
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


seceret_key = "mysecretkey"
hash_password = "HS256"
expire_minutes = 30

app = FastAPI()

context = CryptContext(schemes=["bcrypt"] , deprecated = "auto")
jwt_token = OAuth2PasswordBearer(tokenUrl="token")

class UserRagister(BaseModel):
   user_name : str
   email : EmailStr
   password_login : str

class UserLogin(BaseModel):
   user_name : str
   password_login : str

class UserResponse(BaseModel):
   user_id : int 
   user_name : str
   email : EmailStr
   created_at : datetime

class CreateTask(BaseModel):
   user_id : int
   title : str
   description : Optional[str] = None
   status : Optional[str] = "pending"
   priority : Optional[str] = "low"
   due_date : date


class UpdateTask(BaseModel):
   task_id : int
   title : str
   description : Optional[str] = None
   status : Optional[str] = "pending"
   priority : Optional[str] = "low"
   due_date : date

# comment text basemodel 

class CommentText(BaseModel):
   task_id : int
   user_id : int
   comment_text : str


def get_connection():
 try:
   return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Naveen@123",
        database="task_management",
        auth_plugin="mysql_native_password"
    )
 except mysql.connector.Error as e:
      raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

# secure jwt authentication 

def create_token(data : dict , expire_time : timedelta):
   try:
      data_copy = data.copy()
      expire = datetime.utcnow() + expire_time
      data_copy.update({"exp":expire})
      token = jwt.encode(data_copy , seceret_key , algorithm= hash_password)
      return token 
   except Exception as e:
      return str(e)


def verify_password(simple_password : str, hashed_password : str):
   try:
      if context.verify(simple_password,hashed_password):
        return True
      else:
         raise HTTPException(status_code=401 , detail= "incorrect password")
   except Exception as e:
      raise HTTPException(status_code=500 , detail= f"password varification failed{str(e)}")


def hashing_password(password):
   try:
      return context.hash(password)
   except Exception as e:
      raise HTTPException(status_code=500 , detail= f"password hashing failed {str(e)}")
   
def verify_token(token: str = Depends(jwt_token)):
    try:
        jwt_decode = jwt.decode(token, seceret_key, algorithms=["HS256"])
        user_id = jwt_decode.get("user_id")  
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        return int(user_id)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# verify admin 

def verify_admin(token :str = Depends(jwt_token)):
   try:
      admin_decode = jwt.decode(token , seceret_key , algorithms=["HS256"])
      user_id = admin_decode.get("user_id")
      if not user_id:
         raise HTTPException(status_code=401, detail="Invalid token")
      
      connection = get_connection()
      cursor = connection.cursor(dictionary=True)
      quarry = "select is_admin from users where user_id = %s"
      value = (user_id,)
      cursor.execute(quarry , value)
      user = cursor.fetchone()

      if not user or user["is_admin"] !=1:
         raise HTTPException(status_code=403 , detail="only access can admin")
      return user_id
   except JWTError:
      raise HTTPException(status_code=401, detail="Invalid or expired token")
   finally:
      cursor.close()
      connection.close()


# ragister user 
@app.post("/register", response_model=List[UserResponse])
def register(users: List[UserRagister]):
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        for user in users:
            hashed_password = hashing_password(user.password_login)

            insert_query = """INSERT INTO users (user_name, email, password_login)
                              VALUES (%s, %s, %s)"""
            values = (user.user_name, user.email, hashed_password)
            cursor.execute(insert_query, values)

        connection.commit()

        user_data = []
        for user in users:
            select_query = """SELECT user_id, user_name, email, created_at FROM users
                              WHERE email = %s"""
            cursor.execute(select_query, (user.email,))
            result = cursor.fetchone()
            if result:
                user_data.append(result)

        return user_data  

    except Exception as e:
        connection.rollback() 
        raise HTTPException(status_code=400, detail=f"User registration failed: {e}")

    finally:
        cursor.close()
        connection.close()
        
# login user

@app.post("/login")

def login(data : OAuth2PasswordRequestForm = Depends()):
 try:
   connection = get_connection()
   cursor = connection.cursor(dictionary=True)
   quarry = """select * from users 
   where user_name = %s"""
   value = (data.username,)
   cursor.execute(quarry , value)
   user = cursor.fetchone()

   if not user or not verify_password(data.password , user["password_login"]):
      raise HTTPException(status_code=401, detail="Invalid credentials")
   access_token = create_token({"sub": user["user_name"], "user_id": user["user_id"]}, timedelta(minutes=expire_minutes))
   return {"token" : access_token}

 except Exception as e:
      raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
 finally:
   cursor.close()
   connection.close()


# Task Management crud operation

@app.post("/create_tasks")

def create_data(user: List[CreateTask] , token: str = Depends(verify_token)):
   try:
      db = get_connection()
      cursor = db.cursor()
      
      create_count = 0
      quarry = """insert into tasks (user_id , title , description ,  status , priority ,  due_date)
      values (%s , %s , %s , %s , %s , %s )"""
      for data in user:
         value = (data.user_id , data. title , data.description , data.status , data.priority , data.due_date)
         cursor.execute(quarry , value)
         if cursor.rowcount>0:
            create_count +=1
      
      db.commit()
      if create_count == 0:
         raise HTTPException(status_code=400 , detail="no data created")
   
      return{"tasks create sucessfully :  task count  : ": len(user)}
   except mysql.connector.Error as e:
      db.rollback() 
      raise HTTPException(status_code=500, detail=f"Database Error: {str(e)}")
   finally:
      cursor.close()
      db.close()


# User-Specific Data

@app.get("/get_tasks")

def get_task(user_id :int = Depends(verify_token)):
   try:
         connection = get_connection()
         cursor = connection.cursor(dictionary=True)
         quarry = "select * from tasks where user_id = %s"
         value = (user_id,)
         cursor.execute(quarry , value)
         task = cursor.fetchall()
         return task
   except mysql.connector.Error as e:
      raise HTTPException(status_code=500, detail=f"Database Error: {str(e)}")
   finally:
      cursor.close()
      connection.close()


@app.put("/update_task")

def update_task(update_user : List[UpdateTask] , token: str = Depends(verify_token)):
   try:
      connection = get_connection()
      cursor = connection.cursor()
      if not update_user:
         raise HTTPException(status_code=400 , detail= "provide  your data")
      
      update_count = 0

      quarry = """update tasks set  title = %s ,description =%s , status = %s , priority = %s , due_date = %s
      where task_id = %s and user_id = %s"""
      for user in update_user:
         values = (user. title , user.description , user.status , user.priority , user.due_date , user.task_id , token)
         cursor.execute(quarry , values)
         if cursor.rowcount > 0:
           update_count +=1
      
      if update_count == 0:
         raise HTTPException(status_code=400 , detail = "no data update")
      connection.commit()
      return {"task update successfully ": update_count}
   except mysql.connector.Error as e:
      connection.rollback()
      raise HTTPException(status_code=500 , detail = f"database error {str(e)}")
   
   finally:
      cursor.close()
      connection.close()


@app.delete("/delete_tasks")

def delete_task(delete_task:List[int] , token: str = Depends(verify_token)):
   try:
      connection = get_connection()
      cursor = connection.cursor()
      if not delete_task:
         raise HTTPException(status_code=400 , detail="provide your data")
      
      delete_count = 0
      quarry = """delete from tasks where task_id = %s
      and user_id = %s"""
      for deletes in delete_task:
         values = (deletes, token)
         cursor.execute(quarry , values)
         if cursor.rowcount > 0:
            delete_count += 1
      
      connection.commit()
      if delete_count == 0:
         raise HTTPException(status_code=400 , detail="no data delete")
      return (f"delete sucessfully{delete_count}")
      
   except mysql.connector.Error as e:
      connection.rollback()
      raise HTTPException(status_code=500 , detail = f"database error {str(e)}")
   finally:
      cursor.close()
      connection.close()


# Task Filtering and Sorting

@app.get("/get_filter_task")

def fiter_data(  status: Optional[str] = None,
    priority: Optional[str] = None,
    due_date: Optional[date] = None,
    sort_by: Optional[str] = None,
    order: Optional[str] = "asc",
    token: str = Depends(verify_token)):
   try:
      connection = get_connection()
      cursor = connection.cursor(dictionary=True)
      quarry = "select * from tasks where user_id = %s"
      values = [token]

      if status and priority and due_date:
         quarry = "select * from tasks where user_id = %s and status = %s and priority = %s and due_date = %s"
         values = [token , status , priority , due_date]
      
      elif status and priority:
         quarry = "select * from tasks where user_id = %s and status = %s and priority = %s"
         values = [token , status , priority]

      elif status and due_date:
         quarry = "select * from tasks where user_id = %s and status = %s and due_date = %s"
         values = [token , status , due_date]

      elif priority and due_date:
         quarry = "select * from tasks where user_id = %s and priority = %s and due_date = %s"
         values = [token , priority , due_date]

      elif status:
         quarry = "SELECT * FROM tasks WHERE user_id = %s AND status = %s"
         values = [token, status]

      elif priority:
         quarry = "SELECT * FROM tasks WHERE user_id = %s AND priority = %s"
         values = [token, priority]

      elif due_date:
         quarry = "SELECT * FROM tasks WHERE user_id = %s AND due_date = %s"
         values = [token, due_date]

      if sort_by in["due_date","priority"]:
         quarry += f" order by {sort_by} {order.upper()}"

      cursor.execute(quarry, tuple(values))
      tasks = cursor.fetchall()
      return tasks
   except mysql.connector.Error as e:
      raise HTTPException(status_code=500 , detail = f"database error {str(e)}")
   finally:
      cursor.close()
      connection.close()


# only use admin access all the task

@app.get("/admin_tasks")

def admin_task(admin_id : int = Depends(verify_admin)):
   try:
     connection = get_connection()
     cursor = connection.cursor(dictionary=True)

     cursor.execute("select * from tasks")
     task = cursor.fetchall()
     return task
   except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
   finally:
        cursor.close()
        connection.close()


@app.delete("/admin/delete_tasks")

def delete_task(task_id : List[int] , admin_id : str = Depends(verify_admin)):
   try:
      if not task_id:
         raise HTTPException(status_code=400 , detail="provide your data")
      
      connection = get_connection()
      cursor = connection.cursor()
      
      delete_count = 0
      quarry = "delete from tasks where task_id = %s"
      for deletes in task_id:
         values = (deletes,)
         cursor.execute(quarry , values)
         if cursor.rowcount > 0:
            delete_count +=1
      connection.commit()

      if delete_count == 0:
         HTTPException(status_code=400 , detail="no data deleted")
      return (f"delete sucessfully{delete_count}")
   except mysql.connector.Error as e:
      connection.rollback()
      raise HTTPException(status_code=500 , detail = f"database error {str(e)}")
   finally:
      cursor.close()
      connection.close()


# promote admin 

@app.post("/promote/users")

def promote_user(user_id : List[int] , admin_id : str = Depends(verify_admin)):
   try:
      if not user_id:
         raise HTTPException(status_code=400 , detail="provide your user_id")
      connection = get_connection()
      cursor = connection.cursor()
      
      admin_count = 0
      quarry = "update users set is_admin = 1 where user_id = %s and is_admin = 0"
      for admin in user_id:
         value = (admin,)
         cursor.execute(quarry , value)
         if cursor.rowcount > 0:
            admin_count +=1
      connection.commit()

      if admin_count == 0:
         raise HTTPException(status_code=400 , detail="User is already an admin or does not exist")
      return (f" promote sucessfully {admin_count}")
   except mysql.connector.Error as e:
      connection.rollback()
      raise HTTPException(status_code=500 , detail = f"database error {str(e)}")
   finally:
      cursor.close()
      connection.close()


# comment section 

@app.post("/add_comment")

def add_comment(text :List[CommentText] , token: str = Depends(verify_token)):
   try:
      connection = get_connection()
      cursor = connection.cursor()
      
      create_count = 0
      quarry = "insert into task_comments (task_id , user_id , comment_text) values (%s , %s ,%s)"
      for comment in text:
         values = (comment.task_id , comment.user_id , comment.comment_text)
         cursor.execute(quarry , values)
         if cursor.rowcount>0:
            create_count +=1
      
      connection.commit()
      if create_count == 0:
         raise HTTPException(status_code=400 , detail="no add comments")
      return ("sucessfully comment add")
   except mysql.connector.Error as e:
      connection.rollback()
      raise HTTPException(status_code=500 , detail = f"database error {str(e)}")
   
   finally:
      cursor.close()
      connection.close()


@app.get("/get_comment/task")

def get_comment(task_id : int , token: str = Depends(verify_token)):
   try:
      if not task_id:
         raise HTTPException(status_code=422 , detail="select your task_id")
         
      connection = get_connection()
      cursor = connection.cursor(dictionary=True)

      quarry = "select comment_text , user_id , created_at from task_comments where task_id = %s  order by created_at desc"
      values = (task_id,)
      cursor.execute(quarry , values)
      comment = cursor.fetchall()
      return comment
   except mysql.connector.Error as e:
      raise HTTPException(status_code=500 , detail = f"database error {str(e)}")
   finally:
      cursor.close()
      connection.close()


# smtp server for email 

smpt_server = "smtp.gmail.com"
port = 587
sender_email = "naveengusain0265@gmail.com"
app_password = "nqvkyyqdgqqjxjuf"

def send_email(recive_mail , subject , massage):
   try:
      msg = MIMEMultipart()
      msg["From"] = sender_email
      msg["To"] = recive_mail
      msg["Subject"] = subject
      msg.attach(MIMEText(massage , "plain"))

      server = smtplib.SMTP(smpt_server , port)
      server.starttls()
      server.login(sender_email , app_password)
      server.sendmail(sender_email , recive_mail , msg.as_string())
      return ("email sucessfully send")
   except Exception as e:
      raise HTTPException(status_code= 400 , detail= f"smtp error {str(e)}")
   finally:
      server.quit()


# post email in due date

@app.get("/mail/send")

def post_email():
   try:
      connection = get_connection()
      cursor = connection.cursor(dictionary=True)

      today = datetime.now().date()
      tomorrow = today + timedelta(days=1)

      quarry = "SELECT t.task_id, t.title, t.due_date, u.email FROM tasks t JOIN users u ON t.user_id = u.user_id WHERE t.due_date IN (%s , %s)"
      value = (today , tomorrow)
      cursor.execute(quarry , value)
      tasks = cursor.fetchall()
      for task in tasks:
         subject = f"task reminder : {task['title']} is due on {task['due_date']}"
         mail_body = f"hello , \n\nyour task {task['title']} is due on {task['due_date']}. Please complete it on time.\n\nThanks!"
         send_email(task["email"] , subject , mail_body)
      return {"message": "Successfully sent email reminders!"} 
   except Exception as e:
      raise HTTPException(status_code= 400 , detail= f"smtp error {str(e)}")
   finally:
      cursor.close()
      connection.close()


