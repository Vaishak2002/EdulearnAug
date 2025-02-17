from django.urls import path

from student.views import StudentCreateView,SigninView,Indexview,CoursedetailView,AddToCartView,CartSummaryView,DeleteFromCartView
from student.views import CheckOutView,MyCoursesView,LessonDetailView,paymentVerificationView,SignoutView

urlpatterns=[
                path("register",StudentCreateView.as_view(),name="student-register"),
                path("signin",SigninView.as_view(),name="student-signin"),
                path("index",Indexview.as_view(),name="student-index"),
                path("courses/<int:pk>",CoursedetailView.as_view(),name="course_detail"),

                path("courses/<int:pk>/add-to-cart",AddToCartView.as_view(),name="add-to-cart"),
                path("cart/summary",CartSummaryView.as_view(),name="cart-summary"),
                path("carts/<int:pk1>/remove",DeleteFromCartView.as_view(),name="cart-item-delete"),
                path("checkout",CheckOutView.as_view(),name="checkout"),
                path("order/mycourse",MyCoursesView.as_view(),name="my-courses"),
                path("course/<int:pk>/watch/",LessonDetailView.as_view(),name="lesson-detail"),
                path("payment-page",CheckOutView.as_view(),name="payment"),
                path("payment/verify",paymentVerificationView.as_view(),name="payment-verify"),
                path("signout",SignoutView.as_view(),name="signout")

]