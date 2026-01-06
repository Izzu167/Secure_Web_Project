from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Task
from .forms import TaskForm  # Pastikan fail forms.py wujud dalam folder tasks
from accounts.models import AuditLog # Import AuditLog untuk rekod aktiviti

# Helper function untuk dapatkan IP Address
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@login_required
def task_list(request):
    # SECURITY: Admin boleh tengok semua, User biasa hanya tengok task sendiri
    if request.user.role == 'admin':
        tasks = Task.objects.all()
    else:
        tasks = Task.objects.filter(user=request.user)
    return render(request, 'tasks/task_list.html', {'tasks': tasks})

@login_required
def task_create(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user # Set pemilik task kepada user yang sedang login
            task.save()

            # --- AUDIT LOG ---
            AuditLog.objects.create(
                user=request.user,
                action=f"Created Task: {task.title}",
                ip_address=get_client_ip(request)
            )
            # -----------------
            return redirect('task_list')
    else:
        form = TaskForm()
    return render(request, 'tasks/task_form.html', {'form': form})

@login_required
def task_update(request, pk):
    # SECURITY (IDOR Prevention):
    # Jika Admin, boleh edit sesiapa punya. Jika User, hanya boleh edit diri sendiri.
    if request.user.role == 'admin':
        task = get_object_or_404(Task, pk=pk)
    else:
        task = get_object_or_404(Task, pk=pk, user=request.user)

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()

            # --- AUDIT LOG ---
            AuditLog.objects.create(
                user=request.user,
                action=f"Updated Task: {task.title}",
                ip_address=get_client_ip(request)
            )
            # -----------------
            return redirect('task_list')
    else:
        form = TaskForm(instance=task)
    return render(request, 'tasks/task_form.html', {'form': form})

@login_required
def task_delete(request, pk):
    # SECURITY (IDOR Prevention):
    if request.user.role == 'admin':
        task = get_object_or_404(Task, pk=pk)
    else:
        task = get_object_or_404(Task, pk=pk, user=request.user)

    if request.method == 'POST':
        task_title = task.title # Simpan tajuk untuk log sebelum delete
        task.delete()

        # --- AUDIT LOG ---
        AuditLog.objects.create(
            user=request.user,
            action=f"Deleted Task: {task_title}",
            ip_address=get_client_ip(request)
        )
        # -----------------
        return redirect('task_list')
    
    return render(request, 'tasks/task_confirm_delete.html', {'task': task})