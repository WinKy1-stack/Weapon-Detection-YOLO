# Test Backend API
# Run this after starting the backend

Write-Host "🧪 Testing Weapon Detection API" -ForegroundColor Cyan
Write-Host "===============================`n" -ForegroundColor Cyan

$BASE_URL = "http://localhost:8000/api/v1"

# Test 1: Health Check
Write-Host "1️⃣ Testing Health Check..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get
    Write-Host "✅ Health Check: $($response.status)" -ForegroundColor Green
    Write-Host "   Version: $($response.version)`n" -ForegroundColor Gray
} catch {
    Write-Host "❌ Backend not running or health check failed" -ForegroundColor Red
    Write-Host "   Please start backend first: cd backend; python -m uvicorn app.main:app --reload`n" -ForegroundColor Yellow
    exit 1
}

# Test 2: Register User
Write-Host "2️⃣ Testing User Registration..." -ForegroundColor Yellow
$registerData = @{
    email = "test@example.com"
    password = "test123456"
    full_name = "Test User"
    is_active = $true
    is_admin = $false
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/auth/register" -Method Post -Body $registerData -ContentType "application/json"
    Write-Host "✅ Registration successful!" -ForegroundColor Green
    Write-Host "   User: $($response.user.email)" -ForegroundColor Gray
    Write-Host "   Token: $($response.access_token.Substring(0, 20))...`n" -ForegroundColor Gray
    $global:TOKEN = $response.access_token
} catch {
    if ($_.Exception.Response.StatusCode -eq 400) {
        Write-Host "⚠️  User already exists, trying login instead...`n" -ForegroundColor Yellow
        
        # Test 3: Login
        Write-Host "3️⃣ Testing User Login..." -ForegroundColor Yellow
        $loginData = "username=test@example.com&password=test123456"
        try {
            $response = Invoke-RestMethod -Uri "$BASE_URL/auth/login" -Method Post -Body $loginData -ContentType "application/x-www-form-urlencoded"
            Write-Host "✅ Login successful!" -ForegroundColor Green
            Write-Host "   User: $($response.user.email)" -ForegroundColor Gray
            Write-Host "   Token: $($response.access_token.Substring(0, 20))...`n" -ForegroundColor Gray
            $global:TOKEN = $response.access_token
        } catch {
            Write-Host "❌ Login failed: $($_.Exception.Message)" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "❌ Registration failed: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

# Test 4: Get Current User
Write-Host "4️⃣ Testing Get Current User..." -ForegroundColor Yellow
try {
    $headers = @{
        "Authorization" = "Bearer $global:TOKEN"
    }
    $response = Invoke-RestMethod -Uri "$BASE_URL/auth/me" -Method Get -Headers $headers
    Write-Host "✅ User info retrieved!" -ForegroundColor Green
    Write-Host "   Email: $($response.email)" -ForegroundColor Gray
    Write-Host "   Name: $($response.full_name)" -ForegroundColor Gray
    Write-Host "   Active: $($response.is_active)`n" -ForegroundColor Gray
} catch {
    Write-Host "❌ Get user failed: $($_.Exception.Message)`n" -ForegroundColor Red
}

# Test 5: Get Available Models
Write-Host "5️⃣ Testing Get Available Models..." -ForegroundColor Yellow
try {
    $headers = @{
        "Authorization" = "Bearer $global:TOKEN"
    }
    $response = Invoke-RestMethod -Uri "$BASE_URL/detection/models" -Method Get -Headers $headers
    Write-Host "✅ Models retrieved!" -ForegroundColor Green
    foreach ($model in $response.models) {
        $status = if ($model.available) { "✅" } else { "❌" }
        Write-Host "   $status $($model.name) - $($model.description)" -ForegroundColor Gray
    }
    Write-Host ""
} catch {
    Write-Host "❌ Get models failed: $($_.Exception.Message)`n" -ForegroundColor Red
}

# Test 6: Get Alerts Stats
Write-Host "6️⃣ Testing Get Alert Statistics..." -ForegroundColor Yellow
try {
    $headers = @{
        "Authorization" = "Bearer $global:TOKEN"
    }
    $response = Invoke-RestMethod -Uri "$BASE_URL/alerts/stats?days=7" -Method Get -Headers $headers
    Write-Host "✅ Alert stats retrieved!" -ForegroundColor Green
    Write-Host "   Total Alerts: $($response.total_alerts)" -ForegroundColor Gray
    Write-Host "   Period: $($response.period_days) days" -ForegroundColor Gray
    if ($response.weapon_distribution.Count -gt 0) {
        Write-Host "   Weapons detected:" -ForegroundColor Gray
        foreach ($item in $response.weapon_distribution) {
            Write-Host "     - $($item.weapon): $($item.count)" -ForegroundColor Gray
        }
    }
    Write-Host ""
} catch {
    Write-Host "❌ Get alerts stats failed: $($_.Exception.Message)`n" -ForegroundColor Red
}

# Test 7: MongoDB Connection
Write-Host "7️⃣ Testing MongoDB Connection..." -ForegroundColor Yellow
try {
    $headers = @{
        "Authorization" = "Bearer $global:TOKEN"
    }
    $response = Invoke-RestMethod -Uri "$BASE_URL/alerts/?limit=1" -Method Get -Headers $headers
    Write-Host "✅ MongoDB connected and working!" -ForegroundColor Green
    Write-Host "   Found $($response.Count) alert(s)`n" -ForegroundColor Gray
} catch {
    Write-Host "❌ MongoDB connection failed: $($_.Exception.Message)`n" -ForegroundColor Red
}

Write-Host "`n✨ API Testing Complete!" -ForegroundColor Green
Write-Host "`n📚 View full API documentation at:" -ForegroundColor Cyan
Write-Host "   http://localhost:8000/api/v1/docs`n" -ForegroundColor White

Write-Host "🎯 Next steps:" -ForegroundColor Cyan
Write-Host "   1. Start frontend: cd frontend; npm run dev" -ForegroundColor White
Write-Host "   2. Open http://localhost:3000" -ForegroundColor White
Write-Host "   3. Login with: test@example.com / test123456" -ForegroundColor White
Write-Host "   4. Upload an image to test detection!`n" -ForegroundColor White
