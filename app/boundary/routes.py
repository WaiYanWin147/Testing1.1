# app/boundary/routes.py
"""
Role-segregated routes that render your friend's HTML templates and call your controllers.
All dashboards & CRUD pages require login.

Conventions:
- Templating uses folders you already have: admin/, csr/, pin/, pm/, auth/
- Controllers: one per user story (imported below)
- Redirect after login handled by AuthController (already implemented)

If any template filename differs, just change the string in render_template().
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.exceptions import NotFound

# --- Auth controller (shared) ---
from app.control.auth_controller import AuthController

# --- UserAdmin controllers (Accounts) ---
from app.control.useradmin_viewUserAccount_controller import UserAdminViewUserAccountController
from app.control.useradmin_searchUserAccount_controller import UserAdminSearchUserAccountController
from app.control.useradmin_createUserAccount_controller import UserAdminCreateUserAccountController
from app.control.useradmin_updateUserAccount_controller import UserAdminUpdateUserAccountController
from app.control.useradmin_suspendUserAccount_controller import UserAdminSuspendUserAccountController
from app.control.useradmin_activateUserAccount_controller import UserAdminActivateUserAccountController

# --- UserAdmin controllers (Profiles) ---
from app.control.useradmin_viewUserProfile_controller import UserAdminViewUserProfileController
from app.control.useradmin_createUserProfile_controller import UserAdminCreateUserProfileController
from app.control.useradmin_updateUserProfile_controller import UserAdminUpdateUserProfileController
from app.control.useradmin_suspendUserProfile_controller import UserAdminSuspendUserProfileController
from app.control.useradmin_activateUserProfile_controller import UserAdminActivateUserProfileController
from app.control.useradmin_searchUserProfile_controller import UserAdminSearchUserProfileController

# --- CSR controllers ---
from app.control.csr_searchRequest_controller import CsrSearchRequestController
from app.control.csr_viewRequest_controller import CsrViewRequestController
from app.control.csr_saveToShortlist_controller import CsrSaveToShortlistController
from app.control.csr_searchShortlist_controller import CsrSearchShortlistController
from app.control.csr_viewShortlist_controller import CsrViewShortlistController
from app.control.csr_searchHistory_controller import CsrSearchHistoryController
from app.control.csr_viewHistory_controller import CsrViewHistoryController
from app.control.csr_removeShortlist_controller import CsrRemoveShortlistController


# --- PIN controllers ---
from app.entity.request import Request
from app.control.pin_createRequest_controller import PinCreateRequestController
from app.control.pin_viewRequest_controller import PinViewRequestController
from app.control.pin_updateRequest_controller import PinUpdateRequestController
from app.control.pin_deleteRequest_controller import PinDeleteRequestController
from app.control.pin_searchRequest_controller import PinSearchRequestController
from app.control.pin_trackViews_controller import PinTrackViewsController
from app.control.pin_trackShortlists_controller import PinTrackShortlistsController

# --- Platform Manager controllers ---
from app.control.platform_viewCategory_controller import PlatformViewCategoryController
from app.control.platform_createCategory_controller import PlatformCreateCategoryController
from app.control.platform_updateCategory_controller import PlatformUpdateCategoryController
from app.control.platform_suspendCategory_controller import PlatformSuspendCategoryController
from app.control.platform_searchCategory_controller import PlatformSearchCategoryController
from app.control.platform_generateDailyReport_controller import PlatformGenerateDailyReportController
from app.control.platform_generateWeeklyReport_controller import PlatformGenerateWeeklyReportController
from app.control.platform_generateMonthlyReport_controller import PlatformGenerateMonthlyReportController

boundary_bp = Blueprint("boundary", __name__)

# ----------------------------------
# HOME & AUTH
# ----------------------------------

@boundary_bp.route("/")
def index():
    # Public landing page (templates/index.html)
    return render_template("index.html")

@boundary_bp.route("/login", methods=["GET", "POST"])
def login():
    # GET renders your friend's login form; POST uses AuthController to log in & redirect by role
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        redirect_to, err = AuthController().login(email, password)
        if err:
            flash(err, "danger")
            return render_template("auth/login.html"), 401
        return redirect(redirect_to or "/")
    return render_template("auth/login.html")

@boundary_bp.route("/logout")
@login_required
def logout():
    AuthController().logout()
    return redirect(url_for("boundary.index"))

# ----------------------------------
# USER ADMIN ROUTES  (/admin/*)
# ----------------------------------

@boundary_bp.route("/admin/dashboard")
@login_required
def admin_dashboard():
    # Simple dashboard page (templates/admin/dashboard.html)
    return render_template("admin/dashboard.html")

# Users list + search
@boundary_bp.route("/admin/users")
@login_required
def admin_users():
    from app.entity.user_account import UserAccount
    from app.control.useradmin_searchUserAccount_controller import UserAdminSearchUserAccountController

    search_query = request.args.get("search", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = 10

    if search_query:
        users = UserAdminSearchUserAccountController().searchAccountByName(search_query)
        total = len(users)
        start = (page - 1) * per_page
        end = start + per_page
        pagination_users = users[start:end]

        # ✅ Define a simple pagination helper dynamically
        class Pagination:
            def __init__(self, page, per_page, total, items):
                self.page = page
                self.per_page = per_page
                self.total = total
                self.items = items
                self.pages = (total + per_page - 1) // per_page
                self.has_prev = page > 1
                self.has_next = page < self.pages
                self.prev_num = page - 1
                self.next_num = page + 1

        pagination = Pagination(page, per_page, total, pagination_users)

    else:
        pagination = UserAccount.query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        "admin/users.html",
        users=pagination.items,
        pagination=pagination,
        search_query=search_query,
    )


# Create user (GET form + POST submit)
@boundary_bp.route("/admin/users/create", methods=["GET", "POST"])
@login_required
def admin_create_user():
    from app.entity.user_profile import UserProfile
    profiles = UserProfile.query.filter_by(isActive=True).all()

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        age = request.form.get("age") or None
        phone = request.form.get("phoneNumber") or None   # ✅ correct field name
        profile_id = request.form.get("profile_id")

        try:
            ok = UserAdminCreateUserAccountController().createUserAccount(
                name, email, password, age, phone, profile_id
            )
            if ok:
                flash("User account created successfully.", "success")
                return redirect(url_for("boundary.admin_users"))
        except Exception as e:
            flash(str(e), "danger")

    return render_template("admin/create_user.html", profiles=profiles)

# view user account detail
@boundary_bp.route("/admin/users/<int:user_id>")
@login_required
def admin_view_user(user_id):
    try:
        user = UserAdminViewUserAccountController().view_user(user_id)
    except Exception as e:
        flash(str(e), "danger")
        return redirect(url_for("boundary.admin_users"))

    if not user:
        flash("User not found.", "warning")
        return redirect(url_for("boundary.admin_users"))

    return render_template("admin/view_user.html", user=user)


@boundary_bp.route("/admin/users/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
def admin_edit_user(user_id):
    from app.entity.user_profile import UserProfile
    from app.entity.user_account import UserAccount
    profiles = UserProfile.query.filter_by(isActive=True).all()
    user = UserAccount.query.get(user_id)

    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("boundary.admin_users"))

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("new_password") or None
        age = request.form.get("age") or None
        phone = request.form.get("phoneNumber") or None
        profile_id = request.form.get("profile_id") or None

        try:
            ok = UserAdminUpdateUserAccountController().updateUserAccount(
                userID=user_id,
                name=name,
                email=email,
                password=password,
                age=age,
                phoneNumber=phone,
                profileID=profile_id
            )
            if ok:
                flash("User updated successfully.", "success")
                return redirect(url_for("boundary.admin_users"))
        except Exception as e:
            flash(str(e), "danger")

    return render_template("admin/edit_user.html", user=user, profiles=profiles)


# Suspend user
@boundary_bp.route("/admin/users/<int:user_id>/suspend", methods=["POST"])
@login_required
def admin_suspend_user(user_id):
    try:
        ok = UserAdminSuspendUserAccountController().suspendUserAccount(user_id)
        if ok:
            flash("User suspended successfully.", "success")
    except Exception as e:
        flash(str(e), "danger")
    return redirect(url_for("boundary.admin_users"))


# Activate user
@boundary_bp.route("/admin/users/<int:user_id>/activate", methods=["POST"])
@login_required
def admin_activate_user(user_id):
    try:
        ok = UserAdminActivateUserAccountController().activateUserAccount(user_id)
        if ok:
            flash("User reactivated successfully.", "success")
    except Exception as e:
        flash(str(e), "danger")
    return redirect(url_for("boundary.admin_users"))

# Profiles list
@boundary_bp.route("/admin/profiles")
@login_required
def admin_profiles():
    page = request.args.get("page", 1, type=int)
    per_page = 10

    from app.entity.user_profile import UserProfile
    pagination = UserProfile.query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        "admin/profiles.html",
        profiles=pagination.items,
        pagination=pagination
    )

# Search users by profile ID
@boundary_bp.route("/admin/search/users-by-profile", methods=["GET"])
@login_required
def admin_search_users_by_profile():
    from app.entity.user_profile import UserProfile
    from app.control.useradmin_searchUserProfile_controller import UserAdminSearchUserProfileController
    
    profile_id = request.args.get("profile_id", type=int)
    # Prevent negative or zero ID
    if profile_id is not None and profile_id < 1:
        flash("Profile ID must be a positive number.", "warning")
        return redirect(url_for('boundary.admin_profiles'))
    page = request.args.get("page", 1, type=int)
    per_page = 10

    users = []
    profile = None
    if profile_id:
        try:
            profile = UserProfile.query.get(profile_id)
            if profile:
                users = UserAdminSearchUserProfileController().searchUserByProfile(profile_id)
            else:
                flash("Profile not found.", "warning")
        except Exception as e:
            flash(str(e), "danger")

    total = len(users)
    start = (page - 1) * per_page
    end = start + per_page
    pagination_users = users[start:end]

    class Pagination:
        def __init__(self, page, per_page, total, items):
            self.page = page
            self.per_page = per_page
            self.total = total
            self.items = items
            self.pages = (total + per_page - 1) // per_page
            self.has_prev = page > 1
            self.has_next = page < self.pages
            self.prev_num = page - 1
            self.next_num = page + 1

    pagination = Pagination(page, per_page, total, pagination_users)
    
    # search second time
    return render_template(
        "admin/profiles.html",
        profiles=[profile],  # show only this one profile row
        pagination=None
    )



# Create profile
@boundary_bp.route("/admin/profiles/create", methods=["GET", "POST"])
@login_required
def admin_create_profile():
    if request.method == "POST":
        name = request.form.get("profile_name")
        desc = request.form.get("description")
        try:
            UserAdminCreateUserProfileController().create_profile(name, desc)
            flash("Profile created.", "success")
            return redirect(url_for("boundary.admin_profiles"))
        except Exception as e:
            flash(str(e), "danger")
    return render_template("admin/create_profile.html")

# View User Profile
@boundary_bp.route("/admin/profiles/<int:profile_id>")
@login_required
def admin_view_profile(profile_id):
    profile = UserAdminViewUserProfileController().view_profile(profile_id)
    if not profile:
        flash("Profile not found.", "danger")
        return redirect(url_for("boundary.admin_profiles"))

    return render_template("admin/view_profile.html", profile=profile)


# Edit profile
@boundary_bp.route("/admin/profiles/<int:profile_id>/edit", methods=["GET", "POST"])
@login_required
def admin_edit_profile(profile_id):
    from app.control.useradmin_viewUserProfile_controller import UserAdminViewUserProfileController
    profile = UserAdminViewUserProfileController().view_profile(profile_id)
    if not profile:
        flash("Profile not found.", "danger")
        return redirect(url_for("boundary.admin_profiles"))

    if request.method == "POST":
        new_profile_id = request.form.get("new_profile_id") or None
        profile_name = request.form.get("profile_name")
        description = request.form.get("description")
        is_active = (request.form.get("is_active") == "on")

        try:
            # ✅ handle activation toggle via respective controller
            UserAdminUpdateUserProfileController().toggleActivation(profile_id, is_active)

            # ✅ handle UML-aligned profile update
            ok = UserAdminUpdateUserProfileController().updateUserProfile(
                profileID=profile_id,
                newProfileID=int(new_profile_id) if new_profile_id else None,
                profileName=profile_name,
                description=description
            )
            if ok:
                flash("Profile updated successfully.", "success")
                return redirect(url_for("boundary.admin_profiles"))
        except Exception as e:
            flash(str(e), "danger")

    return render_template("admin/edit_profile.html", profile=profile)

# Suspend / Activate profile
@boundary_bp.route("/admin/profiles/<int:profile_id>/suspend")
@login_required
def admin_suspend_profile(profile_id):
    UserAdminSuspendUserProfileController().suspend_profile(profile_id)
    flash("Profile suspended.", "warning")
    return redirect(url_for("boundary.admin_profiles"))

@boundary_bp.route("/admin/profiles/<int:profile_id>/activate")
@login_required
def admin_activate_profile(profile_id):
    UserAdminActivateUserProfileController().activate_profile(profile_id)
    flash("Profile activated.", "success")
    return redirect(url_for("boundary.admin_profiles"))


# ----------------------------------
# CSR ROUTES  (/csr/*)
# ----------------------------------

@boundary_bp.route("/csr/dashboard")
@login_required
def csr_dashboard():
    return render_template("csr/dashboard.html")

@boundary_bp.route("/csr/requests")
@login_required
def csr_requests():
    from app.control.csr_searchRequest_controller import CsrSearchRequestController
    from app.entity.category import Category

    # pagination params
    page = request.args.get("page", 1, type=int)
    per_page = 9

    # selected filter value
    selected_category = request.args.get("category")

    # fetch all active categories for dropdown
    categories = Category.query.filter_by(isActive=True).all()

    # get filtered results
    results = CsrSearchRequestController().searchRequest(selected_category)
    
    # paginate manually (since we already filtered)
    total = len(results)
    start = (page - 1) * per_page
    end = start + per_page
    paginated = results[start:end]

    class SimplePagination:
        def __init__(self, page, per_page, total):
            self.page = page
            self.per_page = per_page
            self.total = total
            self.pages = (total + per_page - 1) // per_page
            self.has_prev = page > 1
            self.has_next = page < self.pages
            self.prev_num = page - 1
            self.next_num = page + 1

    pagination = SimplePagination(page, per_page, total)

    return render_template(
        "csr/requests.html",
        requests=paginated,
        categories=categories,
        selected_category=selected_category,
        pagination=pagination
    )


@boundary_bp.route("/csr/requests/<int:request_id>")
@login_required
def csr_view_request(request_id):
    from app.control.csr_viewRequest_controller import CsrViewRequestController
    try:
        r = CsrViewRequestController().viewRequestDetails(request_id)
    except Exception as e:
        flash(str(e), "danger")
        return redirect(url_for("boundary.csr_requests"))

    return render_template("csr/view_request.html", request=r)

@boundary_bp.route("/csr/requests/<int:request_id>/shortlist", methods=["POST"])
@login_required
def csr_shortlist_add(request_id):
    ok = CsrSaveToShortlistController().saveToShortlist(request_id, current_user.userID)
    if ok:
        flash("Request added to shortlist.", "success")
    else:
        flash("This request is already in your shortlist.", "info")
    return redirect(url_for("boundary.csr_requests"))

@boundary_bp.route("/csr/shortlist")
@login_required
def csr_shortlist():
    page = request.args.get("page", 1, type=int)
    per_page = 10

    pagination = CsrViewShortlistController().viewShortlist(current_user.userID, page, per_page)

    # extract associated requests directly for rendering convenience
    requests = [s.request for s in pagination.items]

    return render_template(
        "csr/shortlist.html",
        requests=requests,
        pagination=pagination
    )


@boundary_bp.route("/csr/matches")
@login_required
def csr_matches():
    from app.control.csr_searchHistory_controller import CsrSearchHistoryController
    from app.entity.category import Category

    # Get filters
    page = request.args.get("page", 1, type=int)
    per_page = 10
    category_filter = request.args.get("category", type=int)
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()

    # Fetch all categories for dropdown
    categories = Category.query.filter_by(isActive=True).all()

    # Apply filters
    results = CsrSearchHistoryController().searchHistory(
        current_user.userID,
        category_filter,
        start_date,
        end_date
    )

    # Pagination
    total = len(results)
    start = (page - 1) * per_page
    end = start + per_page
    paginated = results[start:end]

    class SimplePagination:
        def __init__(self, page, per_page, total):
            self.page = page
            self.per_page = per_page
            self.total = total
            self.pages = (total + per_page - 1) // per_page
            self.has_prev = page > 1
            self.has_next = page < self.pages
            self.prev_num = page - 1
            self.next_num = page + 1

    pagination = SimplePagination(page, per_page, total)

    return render_template(
        "csr/matches.html",
        matches=paginated,
        categories=categories,
        selected_category=category_filter,
        start_date=start_date,
        end_date=end_date,
        pagination=pagination
    )




@boundary_bp.route("/csr/shortlist/<int:request_id>/remove", methods=["POST"])
@login_required
def csr_shortlist_remove(request_id):
    try:
        CsrRemoveShortlistController().removeFromShortlist(current_user.userID, request_id)
        flash("Removed from shortlist.", "warning")
    except ValueError as e:
        flash(str(e), "danger")
    except Exception as e:
        flash(f"Unexpected error: {e}", "danger")
    return redirect(url_for("boundary.csr_shortlist"))


# ----------------------------------
# PIN ROUTES  (/pin/*)
# ----------------------------------

@boundary_bp.route("/pin/dashboard")
@login_required
def pin_dashboard():
    stats = {
        "total": Request.query.filter_by(pinID=current_user.userID).count(),
        "draft": Request.query.filter_by(pinID=current_user.userID, status="draft").count(),
        "open": Request.query.filter_by(pinID=current_user.userID, status="open").count(),
        "completed": Request.query.filter_by(pinID=current_user.userID, status="completed").count(),
    }

    # if you also have matches_count used in template:
    matches_count = stats["completed"]

    return render_template(
        "pin/dashboard.html",
        stats=stats,
        matches_count=matches_count
    )

@boundary_bp.route("/pin/requests")
@login_required
def pin_requests():
    from app.control.pin_searchRequest_controller import PinSearchRequestController
    from app.entity.category import Category

    # --- pagination ---
    page = request.args.get("page", 1, type=int)
    per_page = 9

    # --- search keyword ---
    search_query = request.args.get("search", "").strip()

    # --- run controller query ---
    controller = PinSearchRequestController()
    all_requests = controller.search_requests(current_user.userID, keyword=search_query)

    # --- paginate manually ---
    total = len(all_requests)
    start = (page - 1) * per_page
    end = start + per_page
    paginated = all_requests[start:end]

    # --- simple pagination helper ---
    class SimplePagination:
        def __init__(self, page, per_page, total):
            self.page = page
            self.per_page = per_page
            self.total = total
            self.pages = (total + per_page - 1) // per_page
            self.has_prev = page > 1
            self.has_next = page < self.pages
            self.prev_num = page - 1
            self.next_num = page + 1

    pagination = SimplePagination(page, per_page, total)

    return render_template(
        "pin/requests.html",
        requests=paginated,
        pagination=pagination,
        search_query=search_query,
    )

@boundary_bp.route("/pin/requests/<int:request_id>")
@login_required
def pin_view_request(request_id):
    from app.control.pin_viewRequest_controller import PinViewRequestController
    try:
        req = PinViewRequestController().viewRequestDetails(request_id)
    except Exception as e:
        flash(str(e), "danger")
        return redirect(url_for("boundary.pin_requests"))

    return render_template("pin/view_request.html", request=req)



@boundary_bp.route("/pin/requests/create", methods=["GET", "POST"])
@login_required
def pin_create_request():
    from app.entity.category import Category
    categories = Category.query.filter_by(isActive=True).all()

    if request.method == "POST":
        category_id = request.form.get("category_id")
        title = request.form.get("title")
        description = request.form.get("description")

        try:
            success = PinCreateRequestController().createRequest(
                userID=current_user.userID,
                categoryID=category_id,
                title=title,
                description=description
            )
            if success:
                flash("Request created successfully.", "success")
                return redirect(url_for("boundary.pin_requests"))
        except Exception as e:
            flash(str(e), "danger")

    return render_template("pin/create_request.html", categories=categories)


@boundary_bp.route("/pin/requests/<int:request_id>/edit", methods=["GET", "POST"])
@login_required
def pin_edit_request(request_id):
    from app.entity.request import Request
    from app.entity.category import Category
    from app.control.pin_updateRequest_controller import PinUpdateRequestController

    req = Request.query.get(request_id)
    if not req or req.pinID != current_user.userID:
        raise NotFound("Request not found or unauthorized.")

    # fetch active categories for dropdown
    categories = Category.query.filter_by(isActive=True).all()

    if request.method == "POST":
        # grab inputs
        title = request.form.get("title")
        description = request.form.get("description")
        status = request.form.get("status")
        category_id = request.form.get("category_id", type=int)

        # NOTE: we are NOT letting user pick newRequestID from the form,
        # so we pass None for that param in UML.
        try:
            PinUpdateRequestController().updateRequest(
                requestID=req.requestID,
                newRequestID=None,                     # not changing PK in UI
                userID=current_user.userID,            # auth
                categoryID=category_id,
                title=title,
                description=description,
                status=status
            )
            flash("Request updated.", "success")
            return redirect(url_for("boundary.pin_requests"))
        except Exception as e:
            flash(str(e), "danger")

    return render_template("pin/edit_request.html", req=req, categories=categories)


@boundary_bp.route("/pin/requests/<int:request_id>/delete", methods=["POST"])
@login_required
def pin_delete_request(request_id):
    from app.control.pin_deleteRequest_controller import PinDeleteRequestController
    try:
        PinDeleteRequestController().deleteRequest(request_id, current_user.userID)
        flash("Request deleted successfully.", "warning")
    except Exception as e:
        flash(str(e), "danger")
    return redirect(url_for("boundary.pin_requests"))


@boundary_bp.route("/pin/match-records", methods=["GET"])
@login_required
def pin_match_records():
    from app.control.pin_searchMatchRecord_controller import PinSearchMatchRecordController

    # Get filters
    category_query = request.args.get("category", "").strip()
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = 10

    # Controller call
    results = PinSearchMatchRecordController().searchMatchRecord(
        current_user.userID, category_query, start_date, end_date
    )

    # Manual pagination
    total = len(results)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_matches = results[start:end]

    class SimplePagination:
        def __init__(self, page, per_page, total):
            self.page = page
            self.per_page = per_page
            self.total = total
            self.pages = (total + per_page - 1) // per_page
            self.has_prev = page > 1
            self.has_next = page < self.pages
            self.prev_num = page - 1
            self.next_num = page + 1

    pagination = SimplePagination(page, per_page, total)

    return render_template(
        "pin/matches.html",
        matches=paginated_matches,
        pagination=pagination,
        category_query=category_query,
        start_date=start_date,
        end_date=end_date
    )


@boundary_bp.route("/pin/requests/<int:request_id>/view-counters")
@login_required
def pin_request_counters(request_id):
    views = PinTrackViewsController().get_view_count(request_id)
    shorts = PinTrackShortlistsController().get_shortlist_count(request_id)
    flash(f"Views: {views} | Shortlisted: {shorts}", "info")
    return redirect(url_for("boundary.pin_requests"))

# ----------------------------------
# PLATFORM MANAGER ROUTES  (/pm/*)
# ----------------------------------

@boundary_bp.route("/pm/dashboard")
@login_required
def pm_dashboard():
    from app.entity.category import Category
    from app.entity.request import Request
    from app.entity.match_record import MatchRecord
    from app.entity.report import Report

    summary = {
        "total_categories": Category.query.count(),
        "total_requests": Request.query.count(),
        "open_requests": Request.query.filter_by(status="open").count(),
        "total_reports": Report.query.count(),
        "total_matches": MatchRecord.query.count(),
    }

    return render_template("pm/dashboard.html", summary=summary)

@boundary_bp.route("/pm/categories")
@login_required
def pm_categories():
    from app.control.platform_searchCategory_controller import PlatformSearchCategoryController
    from app.entity.category import Category

    q = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = 10

    # Base query
    if q:
        query = Category.query.filter(Category.categoryName.ilike(f"%{q}%"))
    else:
        query = Category.query

    pagination = query.order_by(Category.categoryName.asc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template(
        "pm/categories.html",
        categories=pagination.items,
        pagination=pagination,
        q=q
    )

@boundary_bp.route("/pm/categories/create", methods=["GET", "POST"])
@login_required
def pm_create_category():
    if request.method == "POST":
        name = request.form.get("category_name")
        desc = request.form.get("description")
        try:
            PlatformCreateCategoryController().create_category(name, desc)
            flash("Category created.", "success")
            return redirect(url_for("boundary.pm_categories"))
        except Exception as e:
            flash(str(e), "danger")
    return render_template("pm/create_category.html")

@boundary_bp.route("/pm/categories/<int:category_id>/edit", methods=["GET", "POST"])
@login_required
def pm_edit_category(category_id):
    from app.entity.category import Category
    cat = Category.query.get(category_id)
    if not cat:
        raise NotFound("Category not found.")

    if request.method == "POST":
        category_name = request.form.get("category_name")
        description = request.form.get("description")

        try:
            PlatformUpdateCategoryController().updateCategory(category_id, category_name, description)
            flash("Category updated successfully.", "success")
            return redirect(url_for("boundary.pm_categories"))
        except Exception as e:
            flash(str(e), "danger")

    return render_template("pm/edit_category.html", category=cat)


@boundary_bp.route("/pm/categories/<int:category_id>/suspend", methods=["POST"])
@login_required
def pm_suspend_category(category_id):
    from app.control.platform_suspendCategory_controller import PlatformSuspendCategoryController
    try:
        PlatformSuspendCategoryController().suspendCategory(category_id)
        flash("Category suspended successfully.", "warning")
    except Exception as e:
        flash(str(e), "danger")
    return redirect(url_for("boundary.pm_categories"))

@boundary_bp.route("/pm/categories/<int:category_id>/activate", methods=["POST"])
@login_required
def pm_activate_category(category_id):
    from app.control.platform_activateCategory_controller import PlatformActivateCategoryController
    try:
        PlatformActivateCategoryController().activateCategory(category_id)
        flash("Category activated successfully.", "success")
    except Exception as e:
        flash(str(e), "danger")
    return redirect(url_for("boundary.pm_categories"))

# Reports
@boundary_bp.route("/pm/reports")
@login_required
def pm_reports():
    page = request.args.get("page", 1, type=int)
    per_page = 10

    from app.entity.report import Report
    pagination = Report.query.order_by(Report.generatedAt.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        "pm/reports.html",
        reports=pagination.items,
        pagination=pagination
    )


@boundary_bp.route("/pm/reports/generate", methods=["GET", "POST"])
@login_required
def pm_generate_report():
    from app.control.platform_generateDailyReport_controller import PlatformGenerateDailyReportController
    from app.control.platform_generateWeeklyReport_controller import PlatformGenerateWeeklyReportController
    from app.control.platform_generateMonthlyReport_controller import PlatformGenerateMonthlyReportController
    from app import db
    if request.method == "POST":
        kind = request.form.get("report_type")  # "daily" | "weekly" | "monthly"
        period = request.form.get("period")     # e.g. "2025-10-26", "2025-W43", "2025-10"
        title = request.form.get("report_title")

        # Pick controller based on kind
        try:
            if kind == "daily":
                report = PlatformGenerateDailyReportController().generateDailyReport(
                    current_user.userID,
                    period
                )
            elif kind == "weekly":
                report = PlatformGenerateWeeklyReportController().generateWeeklyReport(
                    current_user.userID,
                    period
                )
            elif kind == "monthly":
                report = PlatformGenerateMonthlyReportController().generateMonthlyReport(
                    current_user.userID,
                    period
                )
            else:
                flash("Invalid report type.", "danger")
                return render_template("pm/generate_report.html")

            # optional: overwrite title with user's custom title
            if title:
                report.reportTitle = title
                db.session.commit()

            flash("Report generated.", "success")
            return redirect(url_for("boundary.pm_reports"))

        except Exception as e:
            flash(f"Failed to generate report: {e}", "danger")
            return render_template("pm/generate_report.html")

    return render_template("pm/generate_report.html")



@boundary_bp.route("/pm/reports/<int:report_id>")
@login_required
def pm_view_report(report_id):
    from app.entity.report import Report
    import json

    report = Report.query.get_or_404(report_id)
    content = json.loads(report.reportData)
    return render_template("pm/view_report.html", report=report, content=content)

