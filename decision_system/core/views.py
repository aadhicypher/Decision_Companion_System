from pathlib import Path
import os
import random
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.hashers import make_password, check_password
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .forms import SignupForm
from .models import (
    Category,
    SubCategory,
    CategoryCriterion,
    Decision,
    Option,
    Criterion,
    Score,
    Result,
    PasswordResetOTP
)

TEMP_RESULT_SESSION_KEY = "latest_result_payload"
PASSWORD_RESET_USER_SESSION_KEY = "password_reset_user_id"
PASSWORD_RESET_VERIFIED_SESSION_KEY = "password_reset_verified"


def _is_other_category(category):
    if not category:
        return False
    normalized = category.name.strip().lower()
    return normalized in {"other", "other decision"}

@login_required
def home_page(request):

    decisions = Decision.objects.filter(
        user=request.user
    ).order_by("-id")

    return render(request, "core/home_page.html", {
        "decisions": decisions
    })

@login_required
def decision_history(request, decision_id):

    decision = get_object_or_404(
        Decision,
        id=decision_id,
        user=request.user
    )

    options = Option.objects.filter(decision=decision)

    result = Result.objects.filter(
        decision=decision
    ).first()

    scores = Score.objects.filter(
        option__decision=decision
    )

    return render(request, "core/history_page.html", {
        "decision": decision,
        "options": options,
        "scores": scores,
        "result": result
    })


def _get_gemini_api_key():
    """Read GEMINI_API_KEY from env, then fallback to project .env."""
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        return api_key

    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return None

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() == "GEMINI_API_KEY":
            return value.strip().strip('"').strip("'")
    return None


# ==============================
# AUTHENTICATION
# ==============================

def _clear_password_reset_session(request):
    request.session.pop(PASSWORD_RESET_USER_SESSION_KEY, None)
    request.session.pop(PASSWORD_RESET_VERIFIED_SESSION_KEY, None)


def login_view(request):
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect("home_page")

    return render(request, "registration/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("login")


def forgot_password_view(request):
    error = None
    success = None

    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        user_model = get_user_model()
        user = user_model.objects.filter(email__iexact=email).first()

        if not user:
            error = "No account found with that email address."
        else:
            otp_code = f"{random.randint(0, 999999):06d}"
            expires_at = timezone.now() + timedelta(minutes=10)

            PasswordResetOTP.objects.filter(user=user, is_used=False).update(is_used=True)
            PasswordResetOTP.objects.create(
                user=user,
                otp_hash=make_password(otp_code),
                expires_at=expires_at
            )

            send_mail(
                subject="Decide Password Reset OTP",
                message=(
                    f"Your OTP to reset the password is: {otp_code}\n"
                    f"This OTP expires at {expires_at.strftime('%Y-%m-%d %H:%M:%S')} UTC."
                ),
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@decide.local"),
                recipient_list=[user.email],
                fail_silently=False,
            )

            request.session[PASSWORD_RESET_USER_SESSION_KEY] = user.id
            request.session[PASSWORD_RESET_VERIFIED_SESSION_KEY] = False
            success = "OTP sent to your email. Enter it to continue."
            return redirect("verify_reset_otp")

    return render(request, "registration/forgot_password.html", {
        "error": error,
        "success": success,
    })


def verify_reset_otp_view(request):
    error = None
    user_id = request.session.get(PASSWORD_RESET_USER_SESSION_KEY)
    if not user_id:
        return redirect("forgot_password")

    user_model = get_user_model()
    user = user_model.objects.filter(id=user_id).first()
    if not user:
        _clear_password_reset_session(request)
        return redirect("forgot_password")

    if request.method == "POST":
        otp = request.POST.get("otp", "").strip()
        otp_record = PasswordResetOTP.objects.filter(
            user=user,
            is_used=False,
            expires_at__gt=timezone.now()
        ).first()

        if not otp_record or not check_password(otp, otp_record.otp_hash):
            error = "Invalid or expired OTP."
        else:
            otp_record.is_used = True
            otp_record.save(update_fields=["is_used"])
            request.session[PASSWORD_RESET_VERIFIED_SESSION_KEY] = True
            return redirect("reset_password")

    return render(request, "registration/verify_otp.html", {
        "email": user.email,
        "error": error,
    })


def reset_password_view(request):
    error = None
    success = None
    user_id = request.session.get(PASSWORD_RESET_USER_SESSION_KEY)
    is_verified = request.session.get(PASSWORD_RESET_VERIFIED_SESSION_KEY, False)

    if not user_id or not is_verified:
        return redirect("forgot_password")

    user_model = get_user_model()
    user = user_model.objects.filter(id=user_id).first()
    if not user:
        _clear_password_reset_session(request)
        return redirect("forgot_password")

    if request.method == "POST":
        new_password = request.POST.get("new_password", "")
        confirm_password = request.POST.get("confirm_password", "")

        if new_password != confirm_password:
            error = "Passwords do not match."
        else:
            try:
                validate_password(new_password, user=user)
                user.set_password(new_password)
                user.save(update_fields=["password"])
                _clear_password_reset_session(request)
                success = "Password updated successfully. Please log in."
                return redirect("login")
            except ValidationError as exc:
                error = " ".join(exc.messages)

    return render(request, "registration/reset_password.html", {
        "error": error,
        "success": success,
    })

def signup(request):
    """User signup view"""
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully! Please log in.")
            return redirect("login")
    else:
        form = SignupForm()
    
    return render(request, "registration/signup.html", {"form": form})


# ==============================
# STEP 1 – Create Decision
# ==============================

@login_required
def decision_form(request):

    categories = Category.objects.all()
    other_category_ids = [
        str(category.id)
        for category in categories
        if _is_other_category(category)
    ]
    errors = []

    if request.method == "POST":
        subcategory_id = request.POST.get("subcategory", "").strip()
        options_input = request.POST.get("options", "").strip()
        context = request.POST.get("context", "").strip()
        category_id = request.POST.get("category", "").strip()
        category = Category.objects.filter(id=category_id).first()
        selected_other = _is_other_category(category)

        # Validation
        if not category_id:
            errors.append("Please select a category")

        if not category:
            errors.append("Invalid category selected")

        if not selected_other and not subcategory_id:
            errors.append("Please select a subcategory")
        
        if not context:
            errors.append("Please enter a decision description")
        
        if not options_input:
            errors.append("Please enter your options")
        else:
            # Check if at least 2 options are provided
            options_list = [opt.strip() for opt in options_input.split(",") if opt.strip()]
            if len(options_list) < 2:
                errors.append("Please enter at least 2 options separated by commas")

        # If there are errors, return the form with error messages
        if errors:
            return render(request, "core/decision_form.html", {
                "categories": categories,
                "other_category_ids": other_category_ids,
                "errors": errors,
                "form_data": {
                    "category": category_id,
                    "subcategory": subcategory_id,
                    "context": context,
                    "options": options_input
                }
            })

        # If validation passes, process the form
        try:
            subcategory = None
            if not selected_other:
                subcategory = SubCategory.objects.get(
                    id=subcategory_id,
                    category_id=category_id
                )

            decision = Decision.objects.create(
                user=request.user,
                subcategory=subcategory,
                context=context
            )

            # Create options
            options_list = [opt.strip() for opt in options_input.split(",")]

            for opt in options_list:
                Option.objects.create(decision=decision, name=opt)

            # Copy template criteria into decision-specific criteria
            if subcategory:
                template_criteria = CategoryCriterion.objects.filter(
                    subcategory=subcategory
                )

                for template in template_criteria:
                    Criterion.objects.create(
                        decision=decision,
                        name=template.name,
                        weight=template.default_weight,
                        is_positive=template.is_positive
                    )

            request.session["decision_id"] = decision.id
            request.session.pop(TEMP_RESULT_SESSION_KEY, None)

            return redirect("questions_page")
        except SubCategory.DoesNotExist:
            errors.append("Invalid subcategory selected")
            return render(request, "core/decision_form.html", {
                "categories": categories,
                "other_category_ids": other_category_ids,
                "errors": errors,
                "form_data": {
                    "category": category_id,
                    "subcategory": subcategory_id,
                    "context": context,
                    "options": options_input
                }
            })

    return render(request, "core/decision_form.html", {
        "categories": categories,
        "other_category_ids": other_category_ids,
        "errors": []
    })


# ==============================
# STEP 2 – Scoring Page
# ==============================
@login_required
def questions_page(request):

    decision_id = request.session.get("decision_id")

    if not decision_id:
        return redirect("decision_form")

    decision = get_object_or_404(Decision, id=decision_id, user=request.user)
    options = decision.options.all()
    criteria = decision.decision_criteria.all()

    if request.method == "POST":

        # Remove old scores
        Score.objects.filter(option__decision=decision).delete()

        # ------------------------------
        # BUILD PRIORITY MAP (DB CRITERIA)
        # ------------------------------
        priority_map = {}
        total_priority = 0
        existing_names = {c.name.strip().lower() for c in criteria}

        for criterion in criteria:
            weight_field = f"weight__{criterion.id}"
            new_weight = request.POST.get(weight_field)

            priority = int(new_weight) if new_weight else criterion.weight

            priority_map[criterion.id] = priority
            total_priority += priority

        # ------------------------------
        # HANDLE MULTIPLE EXTRA CRITERIA
        # ------------------------------
        extra_criteria = []
        seen_extra_names = set()

        for key in request.POST.keys():
            if key.startswith("extra_name_"):
                index = key.split("_")[-1]
                name = request.POST.get(f"extra_name_{index}", "").strip()

                if not name:
                    continue

                # Avoid duplicates with existing criteria
                normalized_name = name.lower()
                if normalized_name in existing_names or normalized_name in seen_extra_names:
                    continue
                seen_extra_names.add(normalized_name)

                weight_input = request.POST.get(f"extra_weight_{index}")
                weight = int(weight_input) if weight_input else 50

                extra_criteria.append({
                    "index": index,
                    "name": name,
                    "weight": weight
                })

                total_priority += weight

        if total_priority <= 0:
            return render(request, "core/questions_page.html", {
                "decision": decision,
                "options": options,
                "criteria": criteria,
                "errors": ["Please add at least one criterion with a positive priority."]
            })

        # ------------------------------
        # SAVE NORMAL SCORES
        # ------------------------------
        for criterion in criteria:
            for option in options:
                field_name = f"{criterion.id}__{option.id}"
                value = request.POST.get(field_name)

                if value:
                    Score.objects.create(
                        option=option,
                        criterion=criterion,
                        value=int(value)
                    )

        # ------------------------------
        # CALCULATE RESULTS
        # ------------------------------
        results = {}
        criterion_breakdown = []
        for option in options:
            total = 0

            option_scores = Score.objects.filter(
                option=option,
                criterion__decision=decision
            )

            # DB criteria contribution
            for score in option_scores:
                raw_priority = priority_map.get(
                    score.criterion.id,
                    score.criterion.weight
                )

                normalized_priority = (
                    raw_priority / total_priority
                    if total_priority > 0 else 0
                )

                normalized_score = score.value / 100
                total += normalized_score * normalized_priority

            # Extra criteria contribution
            for extra in extra_criteria:
                extra_score_field = f"extra_{extra['index']}__{option.id}"
                extra_score_value = request.POST.get(extra_score_field)

                if extra_score_value:
                    normalized_extra_priority = (
                        extra["weight"] / total_priority
                        if total_priority > 0 else 0
                    )

                    extra_score = int(extra_score_value) / 100
                    total += extra_score * normalized_extra_priority

            results[option] = round(total, 4)

        # Build criterion breakdown for result page using submitted priorities
        for criterion in criteria:
            raw_priority = priority_map.get(criterion.id, criterion.weight)
            normalized_priority = (
                raw_priority / total_priority
                if total_priority > 0 else 0
            )
            rows = []
            best_score = -1
            best_option_id = None

            for option in options:
                score_obj = Score.objects.filter(
                    option=option,
                    criterion=criterion
                ).first()
                raw_value = score_obj.value if score_obj else 0
                weighted = round((raw_value / 100) * normalized_priority, 4)
                rows.append({
                    "option_id": option.id,
                    "option_name": option.name,
                    "raw_value": raw_value,
                    "weighted": weighted
                })
                if weighted > best_score:
                    best_score = weighted
                    best_option_id = option.id

            criterion_breakdown.append({
                "id": f"crit_{criterion.id}",
                "name": criterion.name,
                "weight": raw_priority,
                "is_custom": False,
                "best_option_id": best_option_id,
                "option_scores": rows
            })

        for extra in extra_criteria:
            normalized_priority = (
                extra["weight"] / total_priority
                if total_priority > 0 else 0
            )
            rows = []
            best_score = -1
            best_option_id = None

            for option in options:
                field = f"extra_{extra['index']}__{option.id}"
                raw_value = int(request.POST.get(field, 0) or 0)
                weighted = round((raw_value / 100) * normalized_priority, 4)
                rows.append({
                    "option_id": option.id,
                    "option_name": option.name,
                    "raw_value": raw_value,
                    "weighted": weighted
                })
                if weighted > best_score:
                    best_score = weighted
                    best_option_id = option.id

            criterion_breakdown.append({
                "id": f"extra_{extra['index']}",
                "name": extra["name"],
                "weight": extra["weight"],
                "is_custom": True,
                "best_option_id": best_option_id,
                "option_scores": rows
            })

        # ------------------------------
        # RANK RESULTS
        # ------------------------------
        ranked_results = sorted(
            results.items(),
            key=lambda x: x[1],
            reverse=True
        )

        best_option = ranked_results[0][0]

        # ------------------------------
        # GEMINI EXPLANATION
        # ------------------------------
        try:
            from google import genai

            api_key = _get_gemini_api_key()
            client = genai.Client(api_key=api_key)

            ranking_text = "\n".join(
                [f"{opt.name}: {score}" for opt, score in ranked_results]
            )
            
            # Build criteria scores for best option
            criteria_scores_text = ""
            for criterion in criteria:
                scores = Score.objects.filter(
                    criterion=criterion,
                    option=best_option
                )
                if scores.exists():
                    score_value = scores.first().value
                    criteria_scores_text += f"{criterion.name}: {score_value}/100\n"

            prompt = f"""
            Decision Context: {decision.context}

            Ranked Results:
            {ranking_text}

            Criteria Scores for Best Option ({best_option.name}):
            {criteria_scores_text}

            Please provide a response in this format:
            "The best option to choose from is {best_option.name} since it has the highest score based on your preferences. 
            It also scored highly on these criteria:
            [Then list each criterion and its score for the best option]"
            
            Make it concise and include all the criteria scores.
            """

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

            explanation = response.text

        except Exception:
            explanation = (
                f"Why is {best_option.name} the best option? "
                f"{best_option.name} scored highest overall with {results[best_option] * 100:.1f}%. "
                f"It performed strongly across the weighted criteria for this decision."
            )

        # ------------------------------
        # SAVE RESULT
        # ------------------------------
        Result.objects.filter(decision=decision).delete()

        Result.objects.create(
            decision=decision,
            chosen_option=best_option,
            total_score=results[best_option],
            explanation=explanation
        )

        request.session[TEMP_RESULT_SESSION_KEY] = {
            "decision_id": decision.id,
            "ranked_results": [
                {
                    "option_id": option.id,
                    "option_name": option.name,
                    "score": score
                }
                for option, score in ranked_results
            ],
            "criterion_breakdown": criterion_breakdown
        }

        return redirect("result_page")

    return render(request, "core/questions_page.html", {
        "decision": decision,
        "options": options,
        "criteria": criteria,
        "errors": []
    })


# ==============================
# STEP 3 – Result Page
# ==============================

@login_required
def result_page(request):

    decision_id = request.session.get("decision_id")

    decision = get_object_or_404(Decision, id=decision_id, user=request.user)
    result = get_object_or_404(Result, decision=decision)

    payload = request.session.get(TEMP_RESULT_SESSION_KEY, {})

    if payload.get("decision_id") == decision.id:
        ranked_results = payload.get("ranked_results", [])
        criterion_breakdown = payload.get("criterion_breakdown", [])
        return render(request, "core/result_page.html", {
            "decision": decision,
            "result": result,
            "ranked_results": ranked_results,
            "criterion_breakdown": criterion_breakdown
        })

    # Fallback: recalculate ranked list from persisted DB scores
    options = decision.options.all()
    criteria = list(decision.decision_criteria.all())
    scores = list(
        Score.objects.filter(option__decision=decision).select_related("option", "criterion")
    )
    results = {option.id: 0 for option in options}
    total_priority = sum(max(c.weight, 0) for c in criteria)

    for score in scores:
        weight = max(score.criterion.weight, 0)
        normalized_priority = (weight / total_priority) if total_priority > 0 else 0
        results[score.option.id] += (score.value / 100) * normalized_priority

    ranked_results = sorted([
        {
            "option_id": option.id,
            "option_name": option.name,
            "score": round(results.get(option.id, 0), 4)
        }
        for option in options
    ], key=lambda row: row["score"], reverse=True)

    criterion_breakdown = []
    for criterion in criteria:
        weight = max(criterion.weight, 0)
        normalized_priority = (weight / total_priority) if total_priority > 0 else 0
        rows = []
        best_score = -1
        best_option_id = None

        for option in options:
            score_obj = next(
                (item for item in scores if item.option_id == option.id and item.criterion_id == criterion.id),
                None
            )
            raw_value = score_obj.value if score_obj else 0
            weighted = round((raw_value / 100) * normalized_priority, 4)
            rows.append({
                "option_id": option.id,
                "option_name": option.name,
                "raw_value": raw_value,
                "weighted": weighted
            })
            if weighted > best_score:
                best_score = weighted
                best_option_id = option.id

        criterion_breakdown.append({
            "id": f"crit_{criterion.id}",
            "name": criterion.name,
            "weight": weight,
            "is_custom": False,
            "best_option_id": best_option_id,
            "option_scores": rows
        })

    return render(request, "core/result_page.html", {
        "decision": decision,
        "result": result,
        "ranked_results": ranked_results,
        "criterion_breakdown": criterion_breakdown
    })


