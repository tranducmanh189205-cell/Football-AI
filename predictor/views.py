import os
import joblib
import numpy as np
from datetime import datetime
from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import League, Team, Match, PredictionHistory

# ==========================================
# 1. LOAD MODEL MACHINE LEARNING
# ==========================================
MODEL_PATH = os.path.join(settings.BASE_DIR, 'predictor', 'ai_engine', 'football_model.pkl')
AI_MODEL = None
if os.path.exists(MODEL_PATH):
    try:
        AI_MODEL = joblib.load(MODEL_PATH)
    except Exception as e:
        print(f"[Football AI] Lỗi nạp model: {e}")
        AI_MODEL = None

# ==========================================
# 2. CHUẨN HÓA TÊN ĐỘI
# ==========================================
TEAM_NAME_MAPPING = {
    "manchester united": "Man United",
    "man utd": "Man United",
    "mu": "Man United",
    "manchester city": "Man City",
    "man city": "Man City",
    "tottenham hotspur": "Tottenham",
    "tottenham": "Tottenham",
    "spurs": "Tottenham",
    "wolverhampton": "Wolves",
    "wolverhampton wanderers": "Wolves",
    "newcastle united": "Newcastle",
    "west ham united": "West Ham",
    "brighton & hove albion": "Brighton",
    "nottingham forest": "Nott'm Forest",
    "sheffield united": "Sheffield United",
    "real madrid": "Real Madrid",
    "barcelona": "Barcelona",
    "barca": "Barcelona",
    "atletico madrid": "Ath Madrid",
    "athletic bilbao": "Ath Bilbao",
    "bayern munich": "Bayern Munich",
    "borussia dortmund": "Dortmund",
    "bayer leverkusen": "Leverkusen",
    "rb leipzig": "RB Leipzig",
    "inter milan": "Inter",
    "ac milan": "Milan",
    "juventus": "Juventus",
    "paris saint germain": "Paris SG",
    "psg": "Paris SG",
}

def normalize_team_name(name):
    clean = name.strip().lower()
    return TEAM_NAME_MAPPING.get(clean, name.strip())

# ==========================================
# 3. TRÍCH XUẤT ĐẶC TRƯNG TỪ DATABASE
# ==========================================
def calculate_team_metrics_from_db(team):
    recent_matches = Match.objects.filter(
        (Q(home_team=team) | Q(away_team=team)) & Q(status='FINISHED')
    ).order_by('-date')[:10]

    if not recent_matches.exists():
        return {
            "form_score": 6.5,
            "avg_goals": 1.4,
            "avg_conceded": 1.2,
            "recent_form_badges": ['W', 'D', 'W', 'L', 'D']
        }

    total_goals_scored = 0
    total_goals_conceded = 0
    form_points = 0
    form_badges = []

    for idx, m in enumerate(recent_matches):
        is_home = (m.home_team == team)
        scored = m.home_score if is_home else m.away_score
        conceded = m.away_score if is_home else m.home_score

        if scored is not None and conceded is not None:
            total_goals_scored += scored
            total_goals_conceded += conceded

            if idx < 5:
                if scored > conceded:
                    form_points += 3
                    form_badges.append('W')
                elif scored == conceded:
                    form_points += 1
                    form_badges.append('D')
                else:
                    form_badges.append('L')

    count = len(recent_matches) if len(recent_matches) > 0 else 1
    avg_goals = round(total_goals_scored / count, 1)
    avg_conceded = round(total_goals_conceded / count, 1)
    form_score = round(min(10.0, max(2.0, (form_points / 15.0) * 10.0)), 1)

    return {
        "form_score": form_score,
        "avg_goals": avg_goals,
        "avg_conceded": avg_conceded,
        "recent_form_badges": form_badges if form_badges else ['W', 'D', 'W', 'L', 'D']
    }

def get_head_to_head_stats(team_a, team_b):
    h2h_matches = Match.objects.filter(
        ((Q(home_team=team_a) & Q(away_team=team_b)) | 
         (Q(home_team=team_b) & Q(away_team=team_a))) & Q(status='FINISHED')
    ).order_by('-date')

    total_games = h2h_matches.count()
    team_a_wins = 0
    team_b_wins = 0
    draws = 0

    for m in h2h_matches:
        if m.home_score is None or m.away_score is None:
            continue
        if m.home_team == team_a:
            if m.home_score > m.away_score: team_a_wins += 1
            elif m.home_score < m.away_score: team_b_wins += 1
            else: draws += 1
        else:
            if m.away_score > m.home_score: team_a_wins += 1
            elif m.away_score < m.home_score: team_b_wins += 1
            else: draws += 1

    recent = []
    for m in h2h_matches[:5]:
        if m.home_score is not None and m.away_score is not None:
            recent.append({
                "date": m.date.strftime("%d/%m/%Y") if m.date else "N/A",
                "home": m.home_team.name,
                "away": m.away_team.name,
                "score": f"{m.home_score} - {m.away_score}"
            })

    return {
        "total_games": total_games,
        "team_a_wins": team_a_wins,
        "team_b_wins": team_b_wins,
        "draws": draws,
        "recent_matches": recent
    }

def generate_ai_analysis(team_name, form, goals, conceded):
    note = []
    if form >= 7.5:
        note.append(f"{team_name} sở hữu phong độ vượt trội")
    elif form >= 5.0:
        note.append(f"{team_name} duy trì sự ổn định tương đối")
    else:
        note.append(f"{team_name} đang trải qua chuỗi trận bất ổn")

    if goals >= 1.8:
        note.append("hàng công dứt điểm rất sắc bén")
    else:
        note.append("khả năng chuyển hóa cơ hội còn hạn chế")

    if conceded <= 1.0:
        note.append("phòng ngự thi đấu chắc chắn.")
    else:
        note.append("hàng thủ để lộ nhiều khoảng trống.")

    return ", ".join(note)

# ==========================================
# 4. VIEW INDEX CHÍNH
# ==========================================
def index(request):
    leagues = League.objects.all().order_by('id')
    selected_league_code = request.GET.get('league', 'E0')

    current_league = League.objects.filter(code=selected_league_code).first()
    if not current_league and leagues.exists():
        current_league = leagues.first()

    today = timezone.now().date()

    if current_league:
        teams = Team.objects.filter(league=current_league).order_by('name')
        if not teams.exists():
            teams = Team.objects.all().order_by('name')

        # Tổng số vòng theo từng giải: Bundesliga và Ligue 1 có 34 vòng; các giải khác có 38 vòng
        total_rounds = 34 if current_league.code in ['D1', 'F1'] else 38
        available_rounds = list(range(1, total_rounds + 1))

        # Xác định vòng đấu cần hiển thị
        selected_round = request.GET.get('round')
        if selected_round:
            try:
                current_round = int(selected_round)
            except ValueError:
                current_round = 1
        else:
            # Tự động tìm trận UPCOMING gần nhất từ hôm nay trở đi
            next_match = Match.objects.filter(
                league=current_league,
                status='UPCOMING',
                date__gte=today
            ).order_by('date', 'kickoff_time').first()

            if next_match and next_match.matchday:
                current_round = next_match.matchday
            else:
                # Nếu không có trận nào trong tương lai, tìm vòng đấu có trận chưa đá nhỏ nhất
                fallback_match = Match.objects.filter(
                    league=current_league,
                    status='UPCOMING'
                ).order_by('matchday').first()
                current_round = fallback_match.matchday if fallback_match and fallback_match.matchday else 1

        # LẤY CÁC TRẬN ĐẤU CỦA VÒNG ĐÃ CHỌN (Không lọc cứng status='UPCOMING' để vòng nào cũng xem được)
        upcoming_matches = Match.objects.filter(
            league=current_league,
            matchday=current_round
        ).select_related('home_team', 'away_team').order_by('date', 'kickoff_time')
    else:
        teams = Team.objects.all().order_by('name')
        upcoming_matches = []
        available_rounds = list(range(1, 39))
        current_round = 1

    recent_history = PredictionHistory.objects.all().order_by('-created_at')[:8]
    total_predictions = PredictionHistory.objects.count()
    completed_evals = PredictionHistory.objects.filter(is_correct__isnull=False).count()
    if completed_evals > 0:
        correct_count = PredictionHistory.objects.filter(is_correct=True).count()
        accuracy_rate = round((correct_count / completed_evals) * 100, 1)
    else:
        accuracy_rate = 68.5

    # ==========================================
    # XỬ LÝ POST / AJAX DỰ ĐOÁN
    # ==========================================
    if request.method == "POST":
        mode = request.POST.get("mode", "auto")
        home_name = request.POST.get("home_name", "").strip()
        away_name = request.POST.get("away_name", "").strip()

        norm_home = normalize_team_name(home_name)
        norm_away = normalize_team_name(away_name)

        home_team = Team.objects.filter(name__icontains=norm_home).first()
        away_team = Team.objects.filter(name__icontains=norm_away).first()

        if not home_team or not away_team:
            return JsonResponse({
                "status": "error",
                "message": "Không tìm thấy thông tin của một trong hai đội bóng!"
            }, status=400)

        default_logo = "https://cdn-icons-png.flaticon.com/512/53/53283.png"
        home_logo = home_team.logo_url if home_team.logo_url else default_logo
        away_logo = away_team.logo_url if away_team.logo_url else default_logo

        if mode == "auto":
            home_metrics = calculate_team_metrics_from_db(home_team)
            away_metrics = calculate_team_metrics_from_db(away_team)

            home_form = home_metrics["form_score"]
            away_form = away_metrics["form_score"]
            home_avg_goals = home_metrics["avg_goals"]
            away_avg_goals = away_metrics["avg_goals"]
            home_avg_conceded = home_metrics["avg_conceded"]
            away_avg_conceded = away_metrics["avg_conceded"]
            home_recent_form = home_metrics["recent_form_badges"]
            away_recent_form = away_metrics["recent_form_badges"]
        else:
            home_form = float(request.POST.get("home_form", 5.0))
            away_form = float(request.POST.get("away_form", 5.0))
            home_avg_goals = float(request.POST.get("home_avg_goals", 1.5))
            away_avg_goals = float(request.POST.get("away_avg_goals", 1.0))
            home_avg_conceded = float(request.POST.get("home_avg_conceded", 1.0))
            away_avg_conceded = float(request.POST.get("away_avg_conceded", 1.2))
            home_recent_form = ['W', 'W', 'D', 'L', 'W']
            away_recent_form = ['L', 'D', 'W', 'L', 'D']

        h2h_data = get_head_to_head_stats(home_team, away_team)

        h2h_rate = (h2h_data["team_a_wins"] / h2h_data["total_games"]) if h2h_data["total_games"] > 0 else 0.33

        if AI_MODEL:
            feature_vector = np.array([[
                (home_form / 10.0) * 3.0,
                (away_form / 10.0) * 3.0,
                home_avg_goals,
                away_avg_goals,
                home_avg_conceded,
                away_avg_conceded,
                h2h_rate
            ]])
            probs = AI_MODEL.predict_proba(feature_vector)[0]
            prob_dict = dict(zip(AI_MODEL.classes_, probs))

            prob_home = round(prob_dict.get('H', 0.45) * 100, 1)
            prob_draw = round(prob_dict.get('D', 0.25) * 100, 1)
            prob_away = round(prob_dict.get('A', 0.30) * 100, 1)
        else:
            diff = (home_form - away_form) * 4.0 + (home_avg_goals - away_avg_goals) * 10.0 + 8.0
            prob_home = round(max(15.0, min(75.0, 42.0 + diff)), 1)
            prob_away = round(max(10.0, min(65.0, 32.0 - diff)), 1)
            prob_draw = round(max(10.0, 100.0 - prob_home - prob_away), 1)

        exp_home = max(0.1, (home_avg_goals * 0.55 + away_avg_conceded * 0.45) * (prob_home / 40.0))
        exp_away = max(0.1, (away_avg_goals * 0.55 + home_avg_conceded * 0.45) * (prob_away / 40.0))

        home_goals = int(round(exp_home))
        away_goals = int(round(exp_away))

        if prob_home >= prob_away and prob_home >= prob_draw:
            if home_goals <= away_goals:
                home_goals = away_goals + 1
            prediction = 'H'
        elif prob_away >= prob_home and prob_away >= prob_draw:
            if away_goals <= home_goals:
                away_goals = home_goals + 1
            prediction = 'A'
        else:
            home_goals = away_goals
            prediction = 'D'

        history_record = PredictionHistory.objects.create(
            home_team=home_team,
            away_team=away_team,
            predicted_home_goals=home_goals,
            predicted_away_goals=away_goals,
            predicted_result=prediction,
            mode=mode
        )

        response_payload = {
            "status": "success",
            "home_name": home_team.name,
            "away_name": away_team.name,
            "home_logo": home_logo,
            "away_logo": away_logo,
            "home_goals": home_goals,
            "away_goals": away_goals,
            "prediction": prediction,
            "prob_home": prob_home,
            "prob_draw": prob_draw,
            "prob_away": prob_away,
            "h2h": h2h_data,
            "home_form": home_form,
            "away_form": away_form,
            "home_avg_goals": home_avg_goals,
            "away_avg_goals": away_avg_goals,
            "home_avg_conceded": home_avg_conceded,
            "away_avg_conceded": away_avg_conceded,
            "home_recent_form": home_recent_form,
            "away_recent_form": away_recent_form,
            "home_form_analysis": generate_ai_analysis(home_team.name, home_form, home_avg_goals, home_avg_conceded),
            "away_form_analysis": generate_ai_analysis(away_team.name, away_form, away_avg_goals, away_avg_conceded),
            "history_item": {
                "id": history_record.id,
                "time": history_record.created_at.strftime("%H:%M - %d/%m"),
                "home": home_team.name,
                "away": away_team.name,
                "score": f"{home_goals} - {away_goals}",
                "mode": mode.upper()
            }
        }

        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse(response_payload)

        context = {
            "leagues": leagues,
            "current_league": current_league,
            "teams": teams,
            "recent_history": recent_history,
            "upcoming_matches": upcoming_matches,
            "available_rounds": available_rounds,
            "current_round": current_round,
            "accuracy_rate": accuracy_rate,
            "total_predictions": total_predictions,
            "active_tab": mode,
            **response_payload
        }
        return render(request, "index.html", context)

    # TRẢ VỀ GIAO DIỆN LẦN ĐẦU (GET)
    first_team = teams.first().name if teams.exists() else "Arsenal"
    second_team = teams[1].name if teams.count() > 1 else "Chelsea"

    return render(request, "index.html", {
        "leagues": leagues,
        "current_league": current_league,
        "teams": teams,
        "recent_history": recent_history,
        "upcoming_matches": upcoming_matches,
        "available_rounds": available_rounds,
        "current_round": current_round,
        "accuracy_rate": accuracy_rate,
        "total_predictions": total_predictions,
        "active_tab": "auto",
        "home_name": first_team,
        "away_name": second_team,
        "home_form": 8.0,
        "away_form": 6.5,
        "home_avg_goals": 2.1,
        "away_avg_goals": 1.2,
        "home_avg_conceded": 0.8,
        "away_avg_conceded": 1.4,
    })

# ==========================================
# 5. API XÓA LỊCH SỬ DỰ ĐOÁN
# ==========================================
@require_POST
def delete_prediction_history(request, item_id):
    try:
        record = PredictionHistory.objects.get(id=item_id)
        record.delete()
        total_remaining = PredictionHistory.objects.count()
        return JsonResponse({"status": "success", "total_predictions": total_remaining})
    except PredictionHistory.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Không tìm thấy bản ghi cần xóa!"}, status=404)

@require_POST
def clear_all_history(request):
    PredictionHistory.objects.all().delete()
    return JsonResponse({"status": "success", "total_predictions": 0})