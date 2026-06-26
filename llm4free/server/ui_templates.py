"""
UI Templates for LLM4Free Server.
Contains HTML/CSS/JS for the landing page and custom Swagger UI.
"""

LANDING_PAGE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LLM4Free API - Your All-in-One AI Toolkit</title>
    <meta name="description" content="Access 90+ AI providers, multi-engine web search, TTS, TTI, and powerful developer tools through one unified OpenAI-compatible API.">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        *, *::before, *::after {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        :root {
            --bg-primary: #0a0a0f;
            --bg-secondary: #12121a;
            --bg-card: rgba(255, 255, 255, 0.03);
            --bg-card-hover: rgba(255, 255, 255, 0.06);
            --text-primary: #ffffff;
            --text-secondary: #a1a1aa;
            --text-muted: #71717a;
            --accent-primary: #6366f1;
            --accent-secondary: #8b5cf6;
            --accent-tertiary: #06b6d4;
            --accent-success: #10b981;
            --border-color: rgba(255, 255, 255, 0.08);
            --border-hover: rgba(255, 255, 255, 0.15);
            --glow-primary: rgba(99, 102, 241, 0.4);
            --glow-secondary: rgba(139, 92, 246, 0.3);
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            overflow-x: hidden;
            min-height: 100vh;
        }

        /* Animated Background */
        .bg-gradient {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            z-index: -1;
            overflow: hidden;
        }

        .bg-gradient::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background:
                radial-gradient(ellipse at 20% 20%, rgba(99, 102, 241, 0.15) 0%, transparent 50%),
                radial-gradient(ellipse at 80% 20%, rgba(139, 92, 246, 0.12) 0%, transparent 50%),
                radial-gradient(ellipse at 50% 80%, rgba(6, 182, 212, 0.1) 0%, transparent 50%);
            animation: gradientMove 20s ease-in-out infinite;
        }

        @keyframes gradientMove {
            0%, 100% { transform: translate(0, 0) rotate(0deg); }
            25% { transform: translate(2%, 2%) rotate(1deg); }
            50% { transform: translate(-1%, 3%) rotate(-1deg); }
            75% { transform: translate(-2%, -1%) rotate(0.5deg); }
        }

        /* Floating Orbs */
        .orb {
            position: fixed;
            border-radius: 50%;
            filter: blur(80px);
            opacity: 0.5;
            animation: float 15s ease-in-out infinite;
            z-index: -1;
        }

        .orb-1 {
            width: 400px;
            height: 400px;
            background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
            top: -100px;
            right: -100px;
            animation-delay: 0s;
        }

        .orb-2 {
            width: 300px;
            height: 300px;
            background: linear-gradient(135deg, var(--accent-tertiary), var(--accent-primary));
            bottom: -50px;
            left: -50px;
            animation-delay: -5s;
        }

        .orb-3 {
            width: 250px;
            height: 250px;
            background: linear-gradient(135deg, var(--accent-secondary), var(--accent-tertiary));
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            animation-delay: -10s;
            opacity: 0.3;
        }

        @keyframes float {
            0%, 100% { transform: translate(0, 0) scale(1); }
            25% { transform: translate(30px, -30px) scale(1.05); }
            50% { transform: translate(-20px, 20px) scale(0.95); }
            75% { transform: translate(20px, 30px) scale(1.02); }
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 2rem;
        }

        /* Header */
        header {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 100;
            padding: 1rem 2rem;
            background: rgba(10, 10, 15, 0.8);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid var(--border-color);
        }

        .header-content {
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-size: 1.5rem;
            font-weight: 800;
            color: var(--text-primary);
            text-decoration: none;
            letter-spacing: -0.03em;
        }

        .logo-icon {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 0 20px var(--glow-primary);
        }

        .logo-icon svg {
            width: 24px;
            height: 24px;
            color: white;
        }

        .nav-links {
            display: flex;
            align-items: center;
            gap: 1.5rem;
        }

        .nav-link {
            color: var(--text-secondary);
            text-decoration: none;
            font-weight: 500;
            font-size: 0.95rem;
            transition: color 0.2s ease;
        }

        .nav-link:hover {
            color: var(--text-primary);
        }

        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            padding: 0.75rem 1.5rem;
            border-radius: 10px;
            font-weight: 600;
            font-size: 0.95rem;
            text-decoration: none;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            cursor: pointer;
            border: none;
        }

        .btn-primary {
            background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
            color: white;
            box-shadow: 0 4px 20px var(--glow-primary);
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 30px var(--glow-primary);
        }

        .btn-secondary {
            background: var(--bg-card);
            color: var(--text-primary);
            border: 1px solid var(--border-color);
        }

        .btn-secondary:hover {
            background: var(--bg-card-hover);
            border-color: var(--border-hover);
            transform: translateY(-2px);
        }

        .btn-ghost {
            background: transparent;
            color: var(--text-secondary);
            padding: 0.5rem 1rem;
        }

        .btn-ghost:hover {
            color: var(--text-primary);
            background: var(--bg-card);
        }

        /* Hero Section */
        .hero {
            padding: 10rem 0 6rem;
            text-align: center;
            position: relative;
        }

        .hero-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 100px;
            font-size: 0.85rem;
            color: var(--text-secondary);
            margin-bottom: 2rem;
            animation: fadeInUp 0.6s ease-out;
        }

        .hero-badge-dot {
            width: 8px;
            height: 8px;
            background: var(--accent-success);
            border-radius: 50%;
            animation: pulse 2s ease-in-out infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(1.2); }
        }

        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        h1 {
            font-size: clamp(2.5rem, 6vw, 4.5rem);
            font-weight: 900;
            line-height: 1.1;
            letter-spacing: -0.03em;
            margin-bottom: 1.5rem;
            animation: fadeInUp 0.6s ease-out 0.1s both;
        }

        .gradient-text {
            background: linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 50%, var(--accent-tertiary) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .hero-description {
            font-size: 1.25rem;
            color: var(--text-secondary);
            max-width: 650px;
            margin: 0 auto 3rem;
            animation: fadeInUp 0.6s ease-out 0.2s both;
        }

        .hero-buttons {
            display: flex;
            gap: 1rem;
            justify-content: center;
            flex-wrap: wrap;
            animation: fadeInUp 0.6s ease-out 0.3s both;
        }

        /* Stats Section */
        .stats {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1.5rem;
            padding: 4rem 0;
            border-top: 1px solid var(--border-color);
            border-bottom: 1px solid var(--border-color);
            margin: 4rem 0;
        }

        @media (max-width: 768px) {
            .stats {
                grid-template-columns: repeat(2, 1fr);
            }
        }

        .stat-item {
            text-align: center;
            padding: 1.5rem;
        }

        .stat-value {
            font-size: 3rem;
            font-weight: 800;
            background: linear-gradient(135deg, var(--accent-primary), var(--accent-tertiary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            line-height: 1;
            margin-bottom: 0.5rem;
        }

        .stat-label {
            font-size: 0.95rem;
            color: var(--text-muted);
            font-weight: 500;
        }

        /* Features Section */
        .features-section {
            padding: 4rem 0;
        }

        .section-header {
            text-align: center;
            margin-bottom: 4rem;
        }

        .section-title {
            font-size: 2.5rem;
            font-weight: 800;
            margin-bottom: 1rem;
            letter-spacing: -0.02em;
        }

        .section-description {
            font-size: 1.1rem;
            color: var(--text-secondary);
            max-width: 600px;
            margin: 0 auto;
        }

        .features-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1.5rem;
        }

        @media (max-width: 1024px) {
            .features-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }

        @media (max-width: 640px) {
            .features-grid {
                grid-template-columns: 1fr;
            }
        }

        .feature-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            padding: 2rem;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }

        .feature-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, var(--accent-primary), transparent);
            opacity: 0;
            transition: opacity 0.3s ease;
        }

        .feature-card:hover {
            transform: translateY(-8px);
            border-color: var(--border-hover);
            background: var(--bg-card-hover);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
        }

        .feature-card:hover::before {
            opacity: 1;
        }

        .feature-icon {
            width: 56px;
            height: 56px;
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 1.5rem;
            transition: all 0.3s ease;
        }

        .feature-icon svg {
            width: 28px;
            height: 28px;
        }

        .feature-icon-1 { background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(99, 102, 241, 0.1)); color: var(--accent-primary); }
        .feature-icon-2 { background: linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(139, 92, 246, 0.1)); color: var(--accent-secondary); }
        .feature-icon-3 { background: linear-gradient(135deg, rgba(6, 182, 212, 0.2), rgba(6, 182, 212, 0.1)); color: var(--accent-tertiary); }
        .feature-icon-4 { background: linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(16, 185, 129, 0.1)); color: var(--accent-success); }
        .feature-icon-5 { background: linear-gradient(135deg, rgba(244, 114, 182, 0.2), rgba(244, 114, 182, 0.1)); color: #f472b6; }
        .feature-icon-6 { background: linear-gradient(135deg, rgba(251, 191, 36, 0.2), rgba(251, 191, 36, 0.1)); color: #fbbf24; }

        .feature-card:hover .feature-icon {
            transform: scale(1.1) rotate(5deg);
        }

        .feature-title {
            font-size: 1.25rem;
            font-weight: 700;
            margin-bottom: 0.75rem;
            color: var(--text-primary);
        }

        .feature-description {
            font-size: 0.95rem;
            color: var(--text-secondary);
            line-height: 1.7;
        }

        /* Code Preview */
        .code-section {
            padding: 4rem 0;
        }

        .code-container {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.3);
        }

        .code-header {
            padding: 1rem 1.5rem;
            background: var(--bg-card);
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .code-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }

        .code-dot-red { background: #ef4444; }
        .code-dot-yellow { background: #eab308; }
        .code-dot-green { background: #22c55e; }

        .code-content {
            padding: 1.5rem;
            font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
            font-size: 0.9rem;
            line-height: 1.8;
            overflow-x: auto;
        }

        .code-line {
            display: flex;
            gap: 1rem;
        }

        .code-line-number {
            color: var(--text-muted);
            user-select: none;
            min-width: 2rem;
            text-align: right;
        }

        .code-keyword { color: #c084fc; }
        .code-string { color: #34d399; }
        .code-comment { color: #6b7280; }
        .code-function { color: #60a5fa; }
        .code-variable { color: #f472b6; }

        /* CTA Section */
        .cta-section {
            padding: 6rem 0;
            text-align: center;
        }

        .cta-card {
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(139, 92, 246, 0.1));
            border: 1px solid var(--border-color);
            border-radius: 24px;
            padding: 4rem;
            position: relative;
            overflow: hidden;
        }

        .cta-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, var(--accent-primary), var(--accent-secondary), transparent);
        }

        .cta-title {
            font-size: 2rem;
            font-weight: 800;
            margin-bottom: 1rem;
        }

        .cta-description {
            font-size: 1.1rem;
            color: var(--text-secondary);
            margin-bottom: 2rem;
            max-width: 500px;
            margin-left: auto;
            margin-right: auto;
        }

        /* Footer */
        footer {
            padding: 3rem 0;
            border-top: 1px solid var(--border-color);
            text-align: center;
        }

        .footer-content {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 1.5rem;
        }

        .footer-links {
            display: flex;
            gap: 2rem;
            flex-wrap: wrap;
            justify-content: center;
        }

        .footer-link {
            color: var(--text-muted);
            text-decoration: none;
            font-size: 0.9rem;
            transition: color 0.2s ease;
        }

        .footer-link:hover {
            color: var(--text-primary);
        }

        .footer-credit {
            color: var(--text-muted);
            font-size: 0.85rem;
        }

        .footer-credit a {
            color: var(--accent-primary);
            text-decoration: none;
        }

        .footer-credit a:hover {
            text-decoration: underline;
        }

        /* Responsive */
        @media (max-width: 768px) {
            header {
                padding: 1rem;
            }

            .nav-links {
                gap: 0.75rem;
            }

            .nav-link {
                display: none;
            }

            .hero {
                padding: 8rem 0 4rem;
            }

            .hero-description {
                font-size: 1.1rem;
            }

            .stats {
                gap: 1rem;
                padding: 2rem 0;
            }

            .stat-value {
                font-size: 2rem;
            }

            .cta-card {
                padding: 2.5rem 1.5rem;
            }
        }
    </style>
</head>
<body>
    <div class="bg-gradient"></div>
    <div class="orb orb-1"></div>
    <div class="orb orb-2"></div>
    <div class="orb orb-3"></div>

    <header>
        <div class="header-content">
            <a href="/" class="logo">
                <div class="logo-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="10"></circle>
                        <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"></polygon>
                    </svg>
                </div>
                LLM4Free
            </a>
            <nav class="nav-links">
                <a href="/docs" class="nav-link">Documentation</a>
                <a href="/v1/models" class="nav-link">Models</a>
                <a href="https://github.com/OEvortex/Webscout" class="btn btn-secondary" target="_blank">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                    </svg>
                    GitHub
                </a>
            </nav>
        </div>
    </header>

    <main>
        <section class="hero container">
            <div class="hero-badge">
                <span class="hero-badge-dot"></span>
                OpenAI-Compatible API Server
            </div>
            <h1>Your All-in-One<br><span class="gradient-text">AI Toolkit</span></h1>
            <p class="hero-description">
                Access 90+ AI providers, multi-engine web search, text-to-speech, image generation,
                and powerful developer tools — all through one unified, production-ready API.
            </p>
            <div class="hero-buttons">
                <a href="/docs" class="btn btn-primary">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                        <polyline points="14 2 14 8 20 8"></polyline>
                        <line x1="16" y1="13" x2="8" y2="13"></line>
                        <line x1="16" y1="17" x2="8" y2="17"></line>
                        <polyline points="10 9 9 9 8 9"></polyline>
                    </svg>
                    API Documentation
                </a>
                <a href="/v1/models" class="btn btn-secondary" target="_blank">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="3"></circle>
                        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
                    </svg>
                    View Models
                </a>
                <a href="https://pypi.org/project/llm4free/" class="btn btn-ghost" target="_blank">
                    pip install llm4free →
                </a>
            </div>
        </section>

        <section class="stats container">
            <div class="stat-item">
                <div class="stat-value">90+</div>
                <div class="stat-label">AI Providers</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">8+</div>
                <div class="stat-label">Search Engines</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">15+</div>
                <div class="stat-label">TTS & TTI Providers</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">100%</div>
                <div class="stat-label">OpenAI Compatible</div>
            </div>
        </section>

        <section class="features-section container">
            <div class="section-header">
                <h2 class="section-title">Everything You Need</h2>
                <p class="section-description">
                    A comprehensive toolkit for AI integration, web scraping, and developer productivity.
                </p>
            </div>

            <div class="features-grid">
                <div class="feature-card">
                    <div class="feature-icon feature-icon-1">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
                            <path d="M2 17l10 5 10-5"></path>
                            <path d="M2 12l10 5 10-5"></path>
                        </svg>
                    </div>
                    <h3 class="feature-title">Multi-Provider LLM Access</h3>
                    <p class="feature-description">
                        Connect to OpenAI, Gemini, Claude, GROQ, DeepInfra, Meta AI, Cohere, and 80+ more providers through a unified interface.
                    </p>
                </div>

                <div class="feature-card">
                    <div class="feature-icon feature-icon-2">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="11" cy="11" r="8"></circle>
                            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                        </svg>
                    </div>
                    <h3 class="feature-title">Multi-Engine Web Search</h3>
                    <p class="feature-description">
                        Search across DuckDuckGo, Bing, Brave, Yahoo, Mojeek, and Wikipedia with AI-powered search integration.
                    </p>
                </div>

                <div class="feature-card">
                    <div class="feature-icon feature-icon-3">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                            <path d="M19.07 4.93a10 10 0 0 1 0 14.14"></path>
                            <path d="M15.54 8.46a5 5 0 0 1 0 7.07"></path>
                        </svg>
                    </div>
                    <h3 class="feature-title">Text-to-Speech</h3>
                    <p class="feature-description">
                        Convert text to natural-sounding speech with multiple providers including Elevenlabs, and various AI-powered TTS engines.
                    </p>
                </div>

                <div class="feature-card">
                    <div class="feature-icon feature-icon-4">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                            <circle cx="8.5" cy="8.5" r="1.5"></circle>
                            <polyline points="21 15 16 10 5 21"></polyline>
                        </svg>
                    </div>
                    <h3 class="feature-title">Image Generation</h3>
                    <p class="feature-description">
                        Generate stunning images with AI art providers. Create visuals from text prompts using state-of-the-art models.
                    </p>
                </div>

                <div class="feature-card">
                    <div class="feature-icon feature-icon-5">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="16 18 22 12 16 6"></polyline>
                            <polyline points="8 6 2 12 8 18"></polyline>
                        </svg>
                    </div>
                    <h3 class="feature-title">Developer Tools</h3>
                    <p class="feature-description">
                        SwiftCLI framework, GitAPI toolkit, LitPrinter console output, Scout web parser, and GGUF model conversion utilities.
                    </p>
                </div>

                <div class="feature-card">
                    <div class="feature-icon feature-icon-6">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"></path>
                        </svg>
                    </div>
                    <h3 class="feature-title">Production Ready</h3>
                    <p class="feature-description">
                        High-performance streaming, robust error handling, tool calling support, and seamless integration with existing OpenAI workflows.
                    </p>
                </div>
            </div>
        </section>

        <section class="code-section container">
            <div class="code-container">
                <div class="code-header">
                    <span class="code-dot code-dot-red"></span>
                    <span class="code-dot code-dot-yellow"></span>
                    <span class="code-dot code-dot-green"></span>
                </div>
                <div class="code-content">
                    <div class="code-line"><span class="code-line-number">1</span><span class="code-comment"># Use any OpenAI-compatible client</span></div>
                    <div class="code-line"><span class="code-line-number">2</span><span class="code-keyword">from</span> openai <span class="code-keyword">import</span> OpenAI</div>
                    <div class="code-line"><span class="code-line-number">3</span></div>
                    <div class="code-line"><span class="code-line-number">4</span><span class="code-variable">client</span> = <span class="code-function">OpenAI</span>(</div>
                    <div class="code-line"><span class="code-line-number">5</span>    base_url=<span class="code-string">"http://localhost:8000/v1"</span>,</div>
                    <div class="code-line"><span class="code-line-number">6</span>    api_key=<span class="code-string">"not-needed"</span></div>
                    <div class="code-line"><span class="code-line-number">7</span>)</div>
                    <div class="code-line"><span class="code-line-number">8</span></div>
                    <div class="code-line"><span class="code-line-number">9</span><span class="code-variable">response</span> = <span class="code-variable">client</span>.chat.completions.<span class="code-function">create</span>(</div>
                    <div class="code-line"><span class="code-line-number">10</span>    model=<span class="code-string">"gpt-4"</span>,  <span class="code-comment"># Works with any provider</span></div>
                    <div class="code-line"><span class="code-line-number">11</span>    messages=[{<span class="code-string">"role"</span>: <span class="code-string">"user"</span>, <span class="code-string">"content"</span>: <span class="code-string">"Hello!"</span>}]</div>
                    <div class="code-line"><span class="code-line-number">12</span>)</div>
                </div>
            </div>
        </section>

        <section class="cta-section container">
            <div class="cta-card">
                <h2 class="cta-title">Ready to Get Started?</h2>
                <p class="cta-description">
                    Explore the API documentation, browse available models, or install LLM4Free to begin building.
                </p>
                <div class="hero-buttons">
                    <a href="/docs" class="btn btn-primary">Explore API Docs</a>
                    <a href="https://github.com/OEvortex/Webscout" class="btn btn-secondary" target="_blank">View on GitHub</a>
                </div>
            </div>
        </section>
    </main>

    <footer>
        <div class="container">
            <div class="footer-content">
                <div class="footer-links">
                    <a href="/docs" class="footer-link">API Documentation</a>
                    <a href="/v1/models" class="footer-link">Models</a>
                    <a href="https://github.com/OEvortex/Webscout" class="footer-link" target="_blank">GitHub</a>
                    <a href="https://pypi.org/project/llm4free/" class="footer-link" target="_blank">PyPI</a>
                    <a href="https://t.me/OEvortexAI" class="footer-link" target="_blank">Telegram</a>
                </div>
                <p class="footer-credit">
                    © 2025 LLM4Free — Made with ❤️ by <a href="https://github.com/OEvortex" target="_blank">OEvortex</a> & Open Source Community
                </p>
            </div>
        </div>
    </footer>
</body>
</html>
"""

SWAGGER_CSS = """
/* LLM4Free Custom Light Swagger Theme */
:root {
    --bg-color: #f8fafc;
    --header-bg: #ffffff;
    --border-color: #e2e8f0;
    --text-primary: #1e293b;
    --text-secondary: #64748b;
    --primary-color: #4f46e5;
    --success-color: #10b981;
    --get-color: #0ea5e9;
    --post-color: #10b981;
}

body {
    background-color: var(--bg-color) !important;
    color: var(--text-primary) !important;
}

.swagger-ui {
    font-family: 'Outfit', system-ui, sans-serif !important;
}

/* Top Bar */
.swagger-ui .topbar {
    background-color: var(--header-bg) !important;
    border-bottom: 1px solid var(--border-color) !important;
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05) !important;
    padding: 15px 0 !important;
}

.swagger-ui .topbar .link {
    display: none !important;
}

/* Main Container */
.swagger-ui .info .title {
    color: var(--text-primary) !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 800 !important;
    letter-spacing: -0.02em !important;
}

.swagger-ui .info p {
    color: var(--text-secondary) !important;
}

.swagger-ui .scheme-container {
    background: var(--header-bg) !important;
    box-shadow: none !important;
    border-bottom: 1px solid var(--border-color) !important;
    border-radius: 8px;
    margin-bottom: 2rem !important;
}

/* Operations - Headers */
.swagger-ui .opblock-tag {
    color: var(--text-primary) !important;
    border-bottom: 1px solid var(--border-color) !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 600 !important;
}

.swagger-ui .opblock-tag small {
    color: var(--text-secondary) !important;
}

/* Operation Blocks */
.swagger-ui .opblock {
    background: #ffffff !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 12px !important;
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05) !important;
    margin: 0 0 20px !important;
    transition: all 0.2s ease !important;
}

.swagger-ui .opblock:hover {
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05) !important;
}

.swagger-ui .opblock .opblock-summary {
    border-bottom: 1px solid transparent !important;
}

.swagger-ui .opblock.is-open .opblock-summary {
    border-bottom: 1px solid var(--border-color) !important;
}

.swagger-ui .opblock .opblock-summary-method {
    border-radius: 6px !important;
    font-family: 'Outfit', monospace !important;
    font-weight: 700 !important;
    min-width: 80px !important;
}

.swagger-ui .opblock .opblock-summary-path {
    color: var(--text-primary) !important;
    font-family: 'Outfit', monospace !important;
    font-weight: 500 !important;
}

.swagger-ui .opblock .opblock-summary-description {
    color: var(--text-secondary) !important;
}

/* GET Method */
.swagger-ui .opblock.opblock-get {
    border-color: rgba(14, 165, 233, 0.2) !important;
}
.swagger-ui .opblock.opblock-get .opblock-summary-method {
    background: #0ea5e9 !important;
}
.swagger-ui .opblock.opblock-get.is-open {
    background: rgba(14, 165, 233, 0.02) !important;
}

/* POST Method */
.swagger-ui .opblock.opblock-post {
    border-color: rgba(16, 185, 129, 0.2) !important;
}
.swagger-ui .opblock.opblock-post .opblock-summary-method {
    background: #10b981 !important;
}
.swagger-ui .opblock.opblock-post.is-open {
    background: rgba(16, 185, 129, 0.02) !important;
}

/* Parameters & Responses */
.swagger-ui .opblock-section-header {
    background: #f8fafc !important;
    margin: 0 !important;
    border-bottom: 1px solid var(--border-color) !important;
}
.swagger-ui .opblock-section-header h4 {
    color: var(--text-primary) !important;
    font-weight: 600 !important;
}

.swagger-ui table thead tr td,
.swagger-ui table thead tr th {
    color: var(--text-secondary) !important;
    border-bottom: 1px solid var(--border-color) !important;
    font-weight: 600 !important;
}

.swagger-ui .parameter__name {
    color: var(--text-primary) !important;
    font-weight: 600 !important;
}

.swagger-ui .parameter__type {
    color: var(--text-secondary) !important;
    font-family: monospace !important;
}

.swagger-ui .parameter__in {
    color: var(--text-secondary) !important;
    font-style: italic !important;
}

/* Models */
.swagger-ui section.models {
    border: 1px solid var(--border-color) !important;
    background: #ffffff !important;
    border-radius: 12px !important;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1) !important;
}

.swagger-ui section.models h4 {
    color: var(--text-primary) !important;
    font-weight: 700 !important;
}

.swagger-ui section.models .model-container {
    background: #ffffff !important;
}

.swagger-ui .model {
    color: var(--text-primary) !important;
}

.swagger-ui .model-title {
    color: var(--text-primary) !important;
}

/* Code Blocks & Inputs */
.swagger-ui .microlight {
    background: #1e293b !important;
    color: #f1f5f9 !important;
    border-radius: 8px !important;
    font-family: 'Consolas', monospace !important;
}

.swagger-ui input,
.swagger-ui textarea,
.swagger-ui select {
    background: #ffffff !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 8px !important;
    padding: 8px 12px !important;
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05) !important;
}

.swagger-ui input:focus,
.swagger-ui textarea:focus,
.swagger-ui select:focus {
    border-color: var(--primary-color) !important;
    outline: 2px solid rgba(79, 70, 229, 0.1) !important;
}

/* Authorize Button */
.swagger-ui .btn.authorize {
    background-color: transparent !important;
    color: var(--primary-color) !important;
    border-color: var(--primary-color) !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}

.swagger-ui .btn.authorize:hover {
    background-color: rgba(79, 70, 229, 0.05) !important;
}

.swagger-ui .btn.authorize svg {
    fill: var(--primary-color) !important;
}

/* Try it out button */
.swagger-ui .btn.try-out__btn {
    background: #ffffff !important;
    border: 1px solid var(--border-color) !important;
    color: var(--text-secondary) !important;
    border-radius: 6px !important;
}

.swagger-ui .btn.try-out__btn:hover {
    background-color: #f8fafc !important;
    color: var(--text-primary) !important;
    border-color: #cbd5e1 !important;
}

.swagger-ui .btn.execute {
    background-color: var(--primary-color) !important;
    border-color: var(--primary-color) !important;
    color: white !important;
    box-shadow: 0 4px 6px -1px rgba(79, 70, 229, 0.3) !important;
    border-radius: 6px !important;
    width: 100% !important;
}

/* Footer override */
.llm4free-footer {
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border-top: 1px solid var(--border-color);
    padding: 12px;
    text-align: center;
    color: var(--text-secondary);
    font-size: 13px;
    z-index: 9999;
    box-shadow: 0 -1px 3px 0 rgba(0, 0, 0, 0.05);
}

.llm4free-footer a {
    color: var(--primary-color);
    text-decoration: none;
    font-weight: 600;
}
"""
