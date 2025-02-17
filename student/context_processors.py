def course_context(request):

    count=0

    if request.user.is_authenticated:


        orders=request.user.purchase.filter(is_paid=True)

        count=len([c for o in orders for c in o.course_objects.all()])

    return {"count":count}

# the context processors must be added in the settings.py's "TEMPLATES" section