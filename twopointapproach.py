# # two point approach in dsa unique element

# def unique(arr):
#     unique = set()
#     le , re = 0 , len(arr) -1
#     while le < re:
#         unique.add(arr[le])
#         unique.add(arr[re])
#         le = le + 1
#         re = re -1
#     return len(unique)
# arr = [1, 1, 2, 2, 3, 4, 4]
# print(unique(arr))


# # two point approach in dsa move zero

# def move_zero(arr):
#     le = 0
#     re = 0
#     while re < len(arr):
#         if arr[re] != 0:
#             arr[le] , arr[re] = arr[re] , arr[le]
#             le = le + 1
#         re = re + 1
#     return arr
# arr = [0, 1, 0, 3, 12]
# print(move_zero(arr))


# # two point approach on dsa subarray sum equal k 


# # import smtplib
# # from email.mime.text import MIMEText
# # from email.mime.multipart import MIMEMultipart

# # server = "smtp.gmail.com"
# # port = 587
# # sender_email = "naveengusain0265@gmail.com"
# # app_password = "nqvkyyqdgqqjxjuf"
# # reciver = "naveengusain0265@gmail.com"

# # massage = MIMEMultipart()
# # massage["from"] = sender_email
# # massage["to"] = reciver #
# # massage["subject"] = "test for smtp" #
# # body = "hello i learn python and my first code in smtp" #

# # massage.attach(MIMEText(body , "plain"))

# # try:
# #     server = smtplib.SMTP(server,port)
# #     server.starttls()
# #     server.login(sender_email ,app_password )
# #     server.sendmail(sender_email , reciver , massage.as_string())
# #     print("email send sucessfully")
# # except Exception as e:
# #     print(f"❌ Error: {e}")
# # finally:
# #     server.quit()


# # Product of Array Except Self  .. 

# def product(arr):
#     n = len(arr)
#     output = [1] * n

#     prefix = 1
#     for j in range(n):
#         output[j] = prefix
#         prefix = prefix*arr[j]
#     suffix = 1
#     for i in range(n-1 , -1 , -1):
#         output[i] = output[i] * suffix
#         suffix = suffix * arr[i]
#     return output
# arr = [1,2,3,4]
# print(product(arr))



# # Sum of Array Except Self
# def sumarray(array):
#     output = []
#     sumarr = sum(array)
#     for num in array:
#         arr = sumarr - num
#         output.append(arr)
#     return output
# array = [1,2,3,4]
# print(sumarray(array))


# # binary search 
# # arr = [5,4,5,1,7,12,45,23,42]
# def binarysearch(arr,target):
#     arr = sorted(arr)
#     strt = 0
#     end = len(arr) - 1
#     while strt <= end:
#         mid = (strt) + (end-strt)//2
#         if arr[mid] < target:
#             strt = mid +1
#         if arr[mid] > target:
#             end = mid -1
#         if arr[mid] ==target:
#          return mid
#     return -1
# arr = [5,4,5,1,7,12,45,23,42]
# target = 23
# print(binarysearch(arr,target))


# # binary serach second question

# # [1, 3, 5, 7, 9, 11, 13]

# def binary(arr , target):
#     start = 0
#     end = len(arr) - 1
#     while start <= end:
#         mid = (start) + (end-start) //2
#         if arr[mid] == target:
#             return mid
#         elif arr[mid] < target:
#             start = mid + 1
#         else:
#             end = mid -1
#     return -1
# arr = [1, 3, 5, 7, 9, 11, 13]
# target = 5
# print(binary(arr , target))


# # recursion binary search
# # [1, 3, 5, 7, 9, 11, 13]

# def recursion_binary(arr , target , start , end):
#     if start > end:
#       return -1

#     mid = (start) + (end - start) // 2
#     if arr[mid] == target:
#         return mid
#     elif arr[mid] < target:
#         return recursion_binary(arr , target , mid+1 , end)
#     else:
#         return recursion_binary(arr , target , start , mid -1)
        
# arr = [1, 3, 5, 7, 9, 11, 13]
# target = 5
# result = recursion_binary(arr , target , 0 , len(arr) -1) 
# print(result)
    

# # serch rotated array:
# # arr = [3,4,5,6,7,0,1,2]

# def array_rotated(arr, target):
#     left = 0
#     right = len(arr) -1
    
#     while left <= right:
#         mid = (left) + (right - left) //2
        
#         if arr[mid] == target:
#             return mid
        
#         if arr[left] <= arr[mid]:                       # if left part is sorted
#             if arr[left] <=target < arr[mid]:
#                right = mid -1
#             else:
#                 left = mid +1

#         if arr[right] >= arr[mid]:                  # if right part is sorted
#             if arr[right] >=target > arr[mid]:
#                 left = mid +1
#             else:
#                 right = mid -1
#     return -1

# arr = [3,4,5,6,7,0,1,2]
# target = 1
# print(array_rotated(arr, target))
            

# # fibonacci

# def fibonacci(num):
#     arr = [0,1]
#     for i in range(2,num):
#         arri = arr[i-1] + arr[i-2]
#         arr.append(arri)
#     return arr
# num = 10
# print(fibonacci(num))



import stripe
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

stripe.api_key =  "sk_test_51RAyGURdFPuXqHhhtXMyZkf2iOXkWSmriUDvDL0NO9DEBctjeC7BBpVoXvi8UP7pZcvXmG4Kazm2A5b76dSXHPrI004xrUhfDG"

class PaymentRequest(BaseModel):
    amount: int    # in rupees
    currency: str = "inr"
    description: str

@app.post("/payment")
def create_pay(payment:PaymentRequest):
    try:
        intent = stripe.PaymentIntent.create(
            amount = payment.amount * 100,
            currency= payment.currency ,
            description= payment.description
        )
        return (
            intent.id,
            intent.client_secret
        )
    except Exception as e:
        return str(e)