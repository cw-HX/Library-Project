"""View functions for the library application.

Each view corresponds to a URL pattern in `library.urls` and handles
request processing, permissions, and rendering templates.
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.http import Http404
from django.contrib.auth.models import User
from django.conf import settings

# Use MongoEngine models for app data
from . import mongo_models
from . import mongo_status
from pymongo.errors import PyMongoError
from .forms import RegisterForm, BookForm
from django.contrib import messages


def home(request):
    """Render the catalog home page listing all books.

    Returns the `library/home.html` template with all Book objects.
    """
    # Check mongo connection status and avoid querying when it's down.
    connected, mongo_err = mongo_status.get_status()
    if not connected:
        return render(request, 'library/home.html', {'books': [], 'mongo_error': mongo_err})

    try:
        books = mongo_models.Book.objects.all()
    except PyMongoError as e:
        # MongoDB operation failed at request time (e.g. auth revoked mid-run).
        # Render the page with an empty list and present the error to the
        # template so the UI stays friendly instead of raising a template
        # iteration error while trying to evaluate the queryset.
        return render(request, 'library/home.html', {'books': [], 'mongo_error': str(e)})
    except Exception as e:
        # Catch-all for other mongoengine/pymongo related runtime errors.
        return render(request, 'library/home.html', {'books': [], 'mongo_error': str(e)})
    return render(request, 'library/home.html', {'books': books})


def register_view(request):
    """Handle new user registration.

    GET: render the registration form.
    POST: validate form input, create a new User instance, set staff
    status when the user selected 'Admin' on the form, log the user in,
    then redirect to the home page.
    """
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            # 'role' is a form-only field; map it to is_staff here for demo purposes
            role = form.cleaned_data.pop('role')
            user = form.save(commit=False)
            if role == 'Admin':
                user.is_staff = True
            user.save()
            login(request, user)
            return redirect('library:home')
    else:
        form = RegisterForm()
    return render(request, 'library/register.html', {'form': form})


def login_view(request):
    """Authenticate a user and start a session.

    POST: Attempt to authenticate using the provided username and
    password. On success, redirect to the catalog. On failure, show an
    error message. GET: render the login form.
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('library:home')
        else:
            messages.error(request, 'Invalid credentials')
    return render(request, 'library/login.html')


def logout_view(request):
    """Log out the current user and redirect to the home page."""
    logout(request)
    return redirect('library:home')


def book_detail(request, pk):
    """Show details for a single book and borrowing state.

    The template receives flags indicating whether copies are available
    and whether the current user has already borrowed this book.
    """
    # pk is the MongoEngine id (as string). Try to fetch the document or 404.
    connected, mongo_err = mongo_status.get_status()
    if not connected:
        # Database not available — present a 404 so templates don't error out.
        raise Http404('Book data not available (MongoDB not connected)')

    try:
        book = mongo_models.Book.objects.get(id=pk)
    except Exception:
        raise Http404('Book not found')

    can_borrow = book.available_copies > 0
    already_borrowed = False
    if request.user.is_authenticated:
        already_borrowed = mongo_models.BorrowRecord.objects(user_id=request.user.id, book_id=book.id, returned=False).count() > 0
    return render(request, 'library/book_detail.html', {'book': book, 'can_borrow': can_borrow, 'already_borrowed': already_borrowed})


@login_required
def borrow_book(request, pk):
    """Create a BorrowRecord if a copy is available.

    Prevents duplicate active borrows for the same user and book. On
    success, redirects the user to their borrows page.
    """
    connected, mongo_err = mongo_status.get_status()
    if not connected:
        messages.error(request, f'Cannot borrow: {mongo_err}')
        return redirect('library:home')

    try:
        book = mongo_models.Book.objects.get(id=pk)
    except Exception:
        messages.error(request, 'Book not found')
        return redirect('library:home')

    # prevent duplicate borrow
    if mongo_models.BorrowRecord.objects(user_id=request.user.id, book_id=book.id, returned=False).count() > 0:
        messages.error(request, 'You have already borrowed this book.')
        return redirect('library:book_detail', pk=pk)
    if book.available_copies <= 0:
        messages.error(request, 'No copies available to borrow.')
        return redirect('library:book_detail', pk=pk)

    br = mongo_models.BorrowRecord(user_id=request.user.id, username=request.user.username, book_id=book.id, book_title=book.title)
    br.save()
    messages.success(request, f'Borrowed "{book.title}"')
    return redirect('library:my_borrows')


@login_required
def return_book(request, pk):
    """Mark a BorrowRecord as returned.

    Staff users can mark any record returned; regular users can only
    return their own records. The view updates the `returned` flag and
    sets `return_date` when performing the return.
    """
    # Allow staff to return any borrow record; regular users can only return their own
    connected, mongo_err = mongo_status.get_status()
    if not connected:
        messages.error(request, f'Cannot return: {mongo_err}')
        return redirect('library:my_borrows')

    try:
        borrow = mongo_models.BorrowRecord.objects.get(id=pk)
    except Exception:
        messages.error(request, 'Borrow record not found')
        return redirect('library:my_borrows')

    if not request.user.is_staff and borrow.user_id != request.user.id:
        messages.error(request, 'You are not allowed to return this record.')
        return redirect('library:my_borrows')

    if borrow.returned:
        messages.info(request, 'Already returned')
    else:
        borrow.returned = True
        borrow.return_date = timezone.now()
        borrow.save()
        messages.success(request, f'Returned "{borrow.book_title}"')
    return redirect('library:my_borrows')


@login_required
def my_borrows(request):
    """Display borrow records.

    - For staff users: group and display all active borrows (returned=False)
      for every user so staff can manage them centrally.
    - For regular users: show only the current user's active borrows.
    """
    # Staff users see all users and their current borrows.
    if request.user.is_staff:
        connected, mongo_err = mongo_status.get_status()
        if not connected:
            # show empty view with error
            return render(request, 'library/my_borrows.html', {'user_borrows': {}, 'is_staff': True, 'mongo_error': mongo_err})

        qs = mongo_models.BorrowRecord.objects(returned=False).order_by('+user_id', '-borrow_date')
        user_borrows = {}
        user_ids = set(r.user_id for r in qs)
        users = {u.id: u for u in User.objects.filter(id__in=list(user_ids))}
        for r in qs:
            user_obj = users.get(r.user_id)
            user_borrows.setdefault(user_obj, []).append(r)
        return render(request, 'library/my_borrows.html', {'user_borrows': user_borrows, 'is_staff': True})

    connected, mongo_err = mongo_status.get_status()
    if not connected:
        messages.error(request, 'Borrow information unavailable: database not connected')
        return render(request, 'library/my_borrows.html', {'records': [], 'is_staff': False, 'mongo_error': mongo_err})

    records = mongo_models.BorrowRecord.objects(user_id=request.user.id, returned=False).order_by('-borrow_date')
    return render(request, 'library/my_borrows.html', {'records': records, 'is_staff': False})


def staff_check(user):
    """Helper used by the `user_passes_test` decorator to verify staff."""
    return user.is_staff


@login_required
@user_passes_test(staff_check)
def admin_book_list(request):
    """Admin listing of all books including counts.

    Only accessible to staff users via the `user_passes_test` decorator.
    """
    connected, mongo_err = mongo_status.get_status()
    if not connected:
        messages.error(request, 'Admin book list unavailable: database not connected')
        return render(request, 'library/admin_book_list.html', {'books': [], 'mongo_error': mongo_err})

    books = mongo_models.Book.objects.all()
    return render(request, 'library/admin_book_list.html', {'books': books})


@login_required
@user_passes_test(staff_check)
def admin_add_book(request):
    """Allow staff to add a new book to the catalog via a form."""
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Book added')
            return redirect('library:admin_book_list')
    else:
        form = BookForm()
    return render(request, 'library/admin_book_form.html', {'form': form, 'action': 'Add'})


@login_required
@user_passes_test(staff_check)
def admin_edit_book(request, pk):
    """Edit an existing book record. Only staff can access."""
    try:
        book = mongo_models.Book.objects.get(id=pk)
    except Exception:
        raise Http404('Book not found')

    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            form.save(instance=book)
            messages.success(request, 'Book updated')
            return redirect('library:admin_book_list')
    else:
        form = BookForm(initial={
            'title': book.title,
            'author': book.author,
            'genre': book.genre,
            'total_copies': book.total_copies,
        })
    return render(request, 'library/admin_book_form.html', {'form': form, 'action': 'Edit'})


@login_required
@user_passes_test(staff_check)
def admin_delete_book(request, pk):
    """Delete a book after confirmation. Staff-only action."""
    try:
        book = mongo_models.Book.objects.get(id=pk)
    except Exception:
        raise Http404('Book not found')

    if request.method == 'POST':
        book.delete()
        messages.success(request, 'Book deleted')
        return redirect('library:admin_book_list')
    return render(request, 'library/confirm_delete.html', {'object': book})
