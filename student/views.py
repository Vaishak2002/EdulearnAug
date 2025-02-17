from django.shortcuts import render,redirect

from django.views.generic import View

from student.forms import StudentCreateForm,SigninForm

from django.views.generic import TemplateView,FormView,CreateView

from django.urls import reverse_lazy,reverse

from django.contrib.auth import authenticate,login,logout

from instructor.models import Course,Cart,Order,Module,Lesson

from django.db.models import Sum

import razorpay

from django.views.decorators.csrf import csrf_exempt

from django.utils.decorators import method_decorator

from student.decorators import signin_required

from decouple import config

RZP_KEY_ID=config('RZP_KEY_ID')

RZP_KEY_SECRET=config("RZP_KEY_SECRET")





# Create your views here.

class StudentCreateView(CreateView):

    # def get(self,request,*args,**kwargs):

    #     form_instance=StudentCreateForm()

    #     return render(request,"studentcreate2.html",{"form":form_instance})
    
    # def post(self,request,*args,**kwargs):

    #     form_data=request.POST

    #     form_instance=StudentCreateForm(form_data)

    #     if form_instance.is_valid():

    #         form_instance.save()

    #         return redirect("student-register")
        
    #     else:

    #         return render(request,"studentcreate2.html",{"form":form_instance})

    template_name="StudentCreate.html"

    form_class=StudentCreateForm

    success_url=reverse_lazy("student-register")


        
class SigninView(FormView):

    # def get(self,request,*args,**kwargs):

    #     form_instance=SigninForm()

    #     return render(request,"signin.html",{"form":form_instance})
    template_name="signin.html"

    form_class=SigninForm

    
    def post(self,request,*args,**kwargs):

        form_data=request.POST

        form_instance=SigninForm(form_data)

        if form_instance.is_valid():

            data=form_instance.cleaned_data

            uname=data.get("username")
            pwd=data.get("password")

            user_obj=authenticate(request,username=uname,password=pwd)

            if user_obj!=None:

                login(request,user_obj)

                return redirect("student-index")
            
            else:

                return render(request,"signin.html",{"form":form_instance})

@method_decorator(signin_required,name="dispatch")           
class Indexview(View):

    def get(self,request,*args,**kwargs):

        all_courses=Course.objects.all()

        purchased_courses=Order.objects.filter(student=request.user).values_list("course_objects",flat=True)

        return render(request,"Home.html",{"courses":all_courses,"purchase_courses":purchased_courses})
    
@method_decorator(signin_required,name="dispatch")    
class CoursedetailView(View):

    def get(self,request,*args,**kwargs):

        id=kwargs.get("pk")

        course_instance=Course.objects.get(id=id)

        return render(request,"course_detail.html",{"course":course_instance})

@method_decorator(signin_required,name="dispatch")    
class AddToCartView(View):

    def get(self,request,*args,**kwargs):

        id=kwargs.get("pk")

        course_instance=Course.objects.get(id=id)

        user_instance=request.user

        # Cart.objects.create(course_object=course_instance,user=user_instance)

        cart_instance,created=Cart.objects.get_or_create(course_object=course_instance,user=user_instance)

        print(created,"=====")

        return redirect("student-index")
    
    # cart summary view

@method_decorator(signin_required,name="dispatch")
class CartSummaryView(View):

        def get(self,request,*args,**kwargs):
            
            qs=request.user.basket.all()

            #  or qs=Cart.objects.filter(user=request.user)

            cart_total=qs.values("course_object__price").aggregate(total=Sum("course_object__price")).get("total") # query to get total sum of price of all the courses==>

            print("===",cart_total)

            return render(request,"cart-summary.html",{"carts":qs,"basket_total":cart_total})

@method_decorator(signin_required,name="dispatch")        
class DeleteFromCartView(View):

    def get(self,request,*args,**kwargs):

        id=kwargs.get("pk1")

        cart_instance=Cart.objects.get(id=id)

        if cart_instance.user != request.user:

            return redirect("student-index")

        Cart.objects.get(id=id).delete()

        return redirect("cart-summary")

    
class CheckOutView(View):

    def get(self,request,*args,**kwargs):

        cart_items=request.user.basket.all()

        order_total=sum([c.course_object.price for c in cart_items])

        order_instance=Order.objects.create(student=request.user,total=order_total)

        for ci in cart_items:

            order_instance.course_objects.add(ci.course_object)

            ci.delete()

        order_instance.save()

        if order_total>0:

            client= razorpay.Client(auth=(RZP_KEY_ID, RZP_KEY_SECRET))

            data = { "amount":int(order_total*100), "currency": "INR", "receipt": "order_rcptid_11" }
            
            payment = client.order.create(data=data) 

            rzp_id=payment.get("id")

            order_instance.rzp_order_id=rzp_id

            order_instance.save()

            context={
                "rzp_key_id":RZP_KEY_ID,
                "amount":order_total,
                "rzp_order_id":rzp_id,
                }

            print(payment,"=================================")

        elif order_total==0:

            order_instance.is_paid=True

            order_instance.save()

            return redirect("my-courses")


        return render(request,"payment.html",context)

@method_decorator(signin_required,name="dispatch")    
class MyCoursesView(View):

    def get(self,request,*args,**kwargs):

        qs=request.user.purchase.filter(is_paid=True)

        return render(request,"mycourse.html",{"orders":qs})
    
#localhost:8000/student/course/1/watch?module=1&lesson-5

@method_decorator(signin_required,name="dispatch")
class LessonDetailView(View):

    def get(self,request,*args,**kwargs):

        course_id=kwargs.get("pk")

        course_instance=Course.objects.get(id=course_id)


# query to not let other users to watch non-purchased course videos
        purchased_courses=request.user.purchase.filter(is_paid=True).values_list("course_objects",flat=True)

        if course_instance.id not in purchased_courses:

            return redirect("student-index")
        

        # retriveing models and lesson from  request.GET
        # request.GET={"module":1,"lesson":4}

        if "module" in request.GET:

            module_id=request.GET.get("module")

        else:

            module_id= course_instance.modules.all().first().id

        module_instance=Module.objects.get(id=module_id,course_object=course_instance)

        if "lesson" in request.GET:

            lesson_id=request.GET.get("lesson") 
            
        else: 
            
            lesson_id=module_instance.lessons.all().first().id

        # print(module_id,"===========")
        # print(lesson_id,"===============")

        lesson_instance=Lesson.objects.get(id=lesson_id,module_object=module_instance)

        return render(request,"lessondetail.html",{"course":course_instance,"lesson":lesson_instance,"module":module_instance})

# this decorator is used to access page without use of :"csrf_token"



@method_decorator(csrf_exempt,name="dispatch")
class paymentVerificationView(View):

    def post(self,request,*args,**kwargs):

        print(request.POST,"==================")

        client=razorpay.Client(auth=(RZP_KEY_ID,RZP_KEY_SECRET))

        try:
            client.utility.verify_payment_signature(request.POST)

            print("payment successful")

            rzp_order_id=request.POST.get("razorpay_order_id")

            order_instance=Order.objects.get(rzp_order_id=rzp_order_id)

            order_instance.is_paid=True

            order_instance.save()

            login(request.order_instance.student)

        except:

            print("print failed")

        return redirect("student-index")

@method_decorator(signin_required,name="dispatch")    
class SignoutView(View):

    def get(self,request,*args,**kwargs):

        logout(request)

        return redirect ("student-signin")

    

        





        














    




                


    








