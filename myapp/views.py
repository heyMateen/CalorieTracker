from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .models import Food, Consume
from .forms import SignUpForm

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
        else:
            # If form is not valid, we'll send it back to template with errors
            return render(request, 'registration/signup.html', {
                'form': form,
                'error_message': 'Please correct the errors below.'
            })
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})


def index(request):
    if not request.user.is_authenticated:
        return redirect('login')  # Redirect to your login page

    foods = Food.objects.all()
    
    if request.method == "POST":
        food_consumed = request.POST.get('food_consumed')
        if food_consumed:
            try:
                consume = Food.objects.get(name=food_consumed)
                Consume.objects.create(user=request.user, food_consumed=consume)
            except Food.DoesNotExist:
                pass  # Handle the case where the food item doesn't exist
        
    consumed_food = Consume.objects.filter(user=request.user)
    return render(request, 'myapp/index.html', {'foods': foods, 'consumed_food': consumed_food})


def delete_consume(request, id):
    if not request.user.is_authenticated:
        return redirect('login')
        
    consumed_food = Consume.objects.get(id=id)
    # Make sure the user owns this consume object
    if consumed_food.user != request.user:
        return redirect('/')
        
    if request.method == 'POST':
        consumed_food.delete()
        return redirect('/')
    return render(request, 'myapp/delete.html')
