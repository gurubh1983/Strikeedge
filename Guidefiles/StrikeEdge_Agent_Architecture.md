# StrikeEdge Multi-Agent Architecture

## Overview

StrikeEdge employs a sophisticated multi-agent AI system designed specifically for options trading. Each agent specializes in a distinct domain, working together to provide research, backtesting, optimization, and real-time trading insights.

---

## Agent Orchestra

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           STRIKEEDGE AGENT ORCHESTRA                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐                                                        │
│  │   ORCHESTRATOR  │◄──── User Requests / Scheduled Jobs                   │
│  │   (Conductor)   │                                                        │
│  └────────┬────────┘                                                        │
│           │                                                                 │
│           ▼                                                                 │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                        SPECIALIST AGENTS                            │    │
│  ├──────────┬──────────┬──────────┬──────────┬──────────┬─────────────┤    │
│  │          │          │          │          │          │             │    │
│  │ 📊       │ 🔬       │ ⚡       │ 📈       │ 🎯       │ 🛡️          │    │
│  │ Market   │ Strategy │ Back-   │ Signal   │ Options  │ Risk        │    │
│  │ Research │ Optimizer│ tester  │ Scanner  │ Analyzer │ Manager     │    │
│  │          │          │          │          │          │             │    │
│  └──────────┴──────────┴──────────┴──────────┴──────────┴─────────────┘    │
│           │                                                                 │
│           ▼                                                                 │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                        SUPPORT AGENTS                               │    │
│  ├────────────────┬────────────────┬────────────────┬─────────────────┤    │
│  │ 🏷️ Strike     │ 📰 News        │ 💹 Greeks      │ 📋 Report       │    │
│  │ Tagger        │ Sentiment      │ Calculator     │ Generator       │    │
│  └────────────────┴────────────────┴────────────────┴─────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Agent Definitions

### 1. 🎭 Orchestrator Agent (Conductor)

**Role**: Master coordinator that manages all agent workflows

**Responsibilities**:
- Receives user requests and scheduled jobs from SQS
- Determines which agents to invoke based on task type
- Manages parallel execution of independent agents
- Aggregates results from all agents
- Handles errors and retries gracefully
- Updates job status throughout execution

**Triggers**:
- User initiates scan/analysis from UI
- Scheduled research jobs (EventBridge)
- Alert conditions met
- Backtest requests

**Tools**:
- `invoke_agent`: Call any specialist agent
- `get_job_status`: Check agent completion
- `store_results`: Save to database
- `send_notification`: Alert user

```python
# Orchestrator decides workflow based on request type
class OrchestratorAgent:
    async def process_request(self, request: Request):
        if request.type == "FULL_ANALYSIS":
            # Parallel: Research + Greeks + Risk
            await asyncio.gather(
                self.invoke("market_researcher", request),
                self.invoke("greeks_calculator", request),
                self.invoke("risk_manager", request)
            )
            # Sequential: Depends on above
            await self.invoke("signal_scanner", request)
            await self.invoke("report_generator", request)
```

---

### 2. 📊 Market Researcher Agent

**Role**: Gather and analyze market intelligence

**Responsibilities**:
- Monitor financial news sources (MoneyControl, Economic Times, NSE)
- Track FII/DII activity and institutional flows
- Analyze sector rotations and market breadth
- Identify trending stocks and unusual activity
- Research earnings, corporate actions, and events
- Store insights in vector knowledge base

**Schedule**: Every 2 hours during market hours (9:00 AM - 3:30 PM IST)

**Data Sources**:
- NSE website (official announcements)
- MoneyControl, Economic Times (news)
- Twitter/X (sentiment)
- Fyers market data

**Tools**:
- `web_search`: Search financial news
- `fetch_url`: Scrape specific pages
- `store_knowledge`: Save to S3 Vectors
- `analyze_sentiment`: NLP sentiment scoring

**Output**: Markdown research reports + structured insights

```python
class MarketResearcherAgent:
    """
    Autonomous agent that continuously gathers market intelligence.
    Runs on schedule, not triggered by user requests.
    """
    
    async def research_cycle(self):
        # 1. Fetch latest news
        news = await self.fetch_financial_news()
        
        # 2. Analyze FII/DII data
        institutional = await self.fetch_institutional_activity()
        
        # 3. Check for unusual options activity
        unusual_oi = await self.detect_unusual_oi()
        
        # 4. Generate insights
        insights = await self.generate_insights(news, institutional, unusual_oi)
        
        # 5. Store in knowledge base
        await self.store_to_vectors(insights)
```

---

### 3. 🔬 Strategy Optimizer Agent

**Role**: Optimize screener parameters for best performance

**Responsibilities**:
- Analyze historical performance of screener configurations
- Suggest optimal indicator thresholds (RSI levels, etc.)
- Recommend timeframe combinations
- Optimize multi-condition filter logic
- Run parameter sweep experiments
- Identify overfitting risks

**Triggers**:
- User requests "Optimize my strategy"
- After backtest completion
- Weekly scheduled optimization

**Algorithms**:
- Grid search for parameter optimization
- Genetic algorithms for complex strategies
- Walk-forward optimization
- Monte Carlo parameter sensitivity

**Tools**:
- `run_backtest`: Execute historical test
- `parameter_sweep`: Test parameter ranges
- `calculate_metrics`: Sharpe, win rate, etc.
- `detect_overfit`: Statistical validation

**Output**: Optimized parameters + performance comparison

```python
class StrategyOptimizerAgent:
    """
    Finds optimal parameters for trading strategies.
    """
    
    async def optimize(self, strategy: Strategy, constraints: dict):
        # Define parameter space
        param_space = {
            "rsi_period": range(10, 20),
            "rsi_threshold": range(55, 75, 5),
            "timeframe": ["5min", "15min", "30min"],
        }
        
        # Run optimization
        results = []
        for params in self.generate_combinations(param_space):
            backtest = await self.run_backtest(strategy, params)
            results.append({
                "params": params,
                "sharpe": backtest.sharpe_ratio,
                "win_rate": backtest.win_rate,
                "max_drawdown": backtest.max_drawdown
            })
        
        # Rank by risk-adjusted returns
        return self.rank_results(results, constraints)
```

---

### 4. ⚡ Backtester Agent

**Role**: Test strategies against historical data

**Responsibilities**:
- Execute trades based on historical signals
- Calculate P&L, win rate, and drawdowns
- Generate performance reports
- Compare against benchmarks (Nifty, BankNifty)
- Simulate realistic execution (slippage, costs)
- Produce equity curves and trade logs

**Triggers**:
- User submits backtest request
- After strategy optimization
- Scheduled nightly backtests for saved strategies

**Metrics Calculated**:
- Total Return, CAGR
- Sharpe Ratio, Sortino Ratio
- Maximum Drawdown
- Win Rate, Profit Factor
- Average Win/Loss
- Expectancy

**Tools**:
- `fetch_historical_data`: Get OHLCV candles
- `compute_indicators`: Calculate RSI, MACD, etc.
- `simulate_trades`: Execute paper trades
- `calculate_metrics`: Performance stats
- `generate_report`: Create backtest report

**Output**: Detailed backtest report with charts

```python
class BacktesterAgent:
    """
    Simulates strategy performance on historical data.
    """
    
    async def backtest(self, strategy: Strategy, period: DateRange):
        # 1. Fetch historical candles for all relevant strikes
        candles = await self.fetch_strike_candles(
            underlyings=strategy.underlyings,
            start=period.start,
            end=period.end
        )
        
        # 2. Calculate indicators
        for strike in candles:
            strike.indicators = self.compute_indicators(strike, strategy.indicators)
        
        # 3. Generate signals
        signals = self.detect_signals(candles, strategy.conditions)
        
        # 4. Simulate trades
        trades = self.simulate_execution(signals, strategy.entry_exit_rules)
        
        # 5. Calculate metrics
        metrics = self.calculate_performance(trades)
        
        # 6. Generate report
        return self.generate_report(trades, metrics)
```

---

### 5. 📈 Signal Scanner Agent

**Role**: Real-time detection of trading signals

**Responsibilities**:
- Monitor all 48,000+ strikes continuously
- Detect indicator crossovers and threshold breaches
- Identify pattern formations
- Correlate signals across timeframes
- Prioritize signals by strength/confidence
- Push alerts to users

**Execution**: Continuous during market hours

**Signal Types**:
- RSI/MACD crossovers on strike charts
- IV spikes and Greeks anomalies
- OI buildup patterns
- Price breakouts
- Volume surges

**Tools**:
- `get_live_candles`: Fetch real-time data
- `compute_indicators`: Calculate technical indicators
- `detect_crossover`: Identify signal events
- `push_alert`: Send notification
- `log_signal`: Store for analysis

**Output**: Real-time signal stream + alerts

```python
class SignalScannerAgent:
    """
    Continuously scans for trading signals across all strikes.
    """
    
    async def scan_cycle(self):
        # Get all user-defined screeners
        screeners = await self.get_active_screeners()
        
        for screener in screeners:
            # Fetch current indicator values
            strikes = await self.get_strikes_with_indicators(
                underlyings=screener.underlyings,
                indicators=screener.indicators
            )
            
            # Check conditions
            matches = []
            for strike in strikes:
                if self.evaluate_conditions(strike, screener.conditions):
                    matches.append(strike)
            
            # Push results
            if matches:
                await self.push_results(screener.user_id, matches)
                await self.log_signals(matches)
```

---

### 6. 🎯 Options Analyzer Agent

**Role**: Deep analysis of options positions and strategies

**Responsibilities**:
- Analyze option chain for specific underlying
- Identify optimal strikes for entry
- Calculate expected value of trades
- Suggest spread strategies (Bull Call, Iron Condor, etc.)
- Analyze max profit/loss scenarios
- Track open interest and volume patterns

**Triggers**:
- User selects underlying for analysis
- Signal detected, needs position sizing
- Portfolio review requests

**Analysis Types**:
- Strike selection optimization
- Strategy comparison (Naked vs Spread)
- Payoff diagram generation
- Break-even analysis
- Probability of profit calculation

**Tools**:
- `fetch_option_chain`: Get all strikes
- `calculate_greeks`: IV, Delta, Gamma, etc.
- `analyze_oi_patterns`: OI buildup analysis
- `suggest_strategy`: Recommend positions
- `generate_payoff`: Create payoff diagrams

**Output**: Option analysis report + strategy recommendations

```python
class OptionsAnalyzerAgent:
    """
    Provides deep analysis for options trading decisions.
    """
    
    async def analyze(self, underlying: str, user_view: str):
        # 1. Fetch option chain
        chain = await self.fetch_option_chain(underlying)
        
        # 2. Calculate Greeks for all strikes
        for strike in chain:
            strike.greeks = self.calculate_greeks(strike)
        
        # 3. Analyze OI patterns
        oi_analysis = self.analyze_oi_buildup(chain)
        
        # 4. Based on user's view (bullish/bearish/neutral)
        strategies = self.suggest_strategies(chain, user_view)
        
        # 5. Calculate payoffs
        for strategy in strategies:
            strategy.payoff = self.calculate_payoff(strategy)
            strategy.probability_of_profit = self.calculate_pop(strategy)
        
        # 6. Generate recommendation
        return self.generate_analysis_report(chain, oi_analysis, strategies)
```

---

### 7. 🛡️ Risk Manager Agent

**Role**: Monitor and manage portfolio risk

**Responsibilities**:
- Calculate portfolio Greeks (aggregate Delta, Gamma, etc.)
- Monitor position sizing limits
- Detect concentration risk
- Alert on excessive exposure
- Suggest hedging strategies
- Track correlation risks

**Triggers**:
- Before any trade execution
- Real-time portfolio monitoring
- Daily risk reports

**Risk Metrics**:
- Portfolio Delta, Gamma, Theta, Vega
- Value at Risk (VaR)
- Maximum position size checks
- Sector/underlying concentration
- Margin utilization

**Tools**:
- `get_portfolio`: Fetch current positions
- `calculate_portfolio_greeks`: Aggregate risk
- `check_limits`: Validate against rules
- `suggest_hedge`: Recommend risk reduction
- `generate_risk_report`: Create report

**Output**: Risk assessment + hedging recommendations

```python
class RiskManagerAgent:
    """
    Monitors and manages portfolio risk.
    """
    
    async def assess_risk(self, portfolio: Portfolio):
        # 1. Calculate aggregate Greeks
        greeks = self.calculate_portfolio_greeks(portfolio)
        
        # 2. Check position limits
        limit_violations = self.check_position_limits(portfolio)
        
        # 3. Calculate VaR
        var = self.calculate_var(portfolio, confidence=0.95)
        
        # 4. Check concentration
        concentration = self.analyze_concentration(portfolio)
        
        # 5. Suggest hedges if needed
        hedges = []
        if greeks.delta > self.max_delta:
            hedges.append(self.suggest_delta_hedge(portfolio))
        
        return RiskReport(
            greeks=greeks,
            var=var,
            violations=limit_violations,
            concentration=concentration,
            suggested_hedges=hedges
        )
```

---

### 8. 🏷️ Strike Tagger Agent

**Role**: Classify and enrich strike data

**Responsibilities**:
- Identify strike type (ITM/ATM/OTM)
- Calculate moneyness
- Determine liquidity score
- Tag with bid-ask spread quality
- Classify by expiry (weekly/monthly)
- Identify arbitrage opportunities

**Triggers**:
- New strikes added to system
- Daily classification update
- Before any analysis

**Uses Structured Outputs**: Yes (consistent JSON format)

```python
class StrikeTaggerAgent:
    """
    Classifies and enriches strike metadata.
    Uses structured outputs for consistency.
    """
    
    class StrikeClassification(BaseModel):
        strike_token: str
        moneyness: Literal["ITM", "ATM", "OTM", "Deep ITM", "Deep OTM"]
        liquidity_score: float  # 0-1
        bid_ask_quality: Literal["Tight", "Normal", "Wide", "Very Wide"]
        expiry_type: Literal["Weekly", "Monthly", "Quarterly"]
        days_to_expiry: int
        
    async def classify(self, strikes: List[Strike]) -> List[StrikeClassification]:
        # LLM classifies with structured output
        pass
```

---

### 9. 📰 News Sentiment Agent

**Role**: Analyze news and social sentiment

**Responsibilities**:
- Fetch news for specific stocks
- Analyze sentiment (bullish/bearish/neutral)
- Score impact magnitude
- Identify event-driven opportunities
- Track social media buzz
- Correlate news with price action

**Schedule**: Every 30 minutes during market hours

**Sources**:
- MoneyControl, Economic Times
- NSE announcements
- Twitter/X financial accounts
- Reddit (IndianStreetBets)

**Tools**:
- `fetch_news`: Get latest articles
- `analyze_sentiment`: NLP scoring
- `score_impact`: Estimate price impact
- `store_sentiment`: Save to database

```python
class NewsSentimentAgent:
    """
    Analyzes news and social sentiment for trading signals.
    """
    
    async def analyze_sentiment(self, underlying: str):
        # 1. Fetch recent news
        news = await self.fetch_news(underlying, hours=24)
        
        # 2. Analyze each article
        sentiments = []
        for article in news:
            sentiment = await self.analyze_article(article)
            sentiments.append(sentiment)
        
        # 3. Aggregate sentiment
        aggregate = self.aggregate_sentiment(sentiments)
        
        # 4. Check for event-driven opportunities
        events = self.identify_events(news)
        
        return SentimentReport(
            underlying=underlying,
            sentiment_score=aggregate.score,  # -1 to 1
            sentiment_label=aggregate.label,  # Bearish/Neutral/Bullish
            confidence=aggregate.confidence,
            key_events=events,
            articles_analyzed=len(news)
        )
```

---

### 10. 💹 Greeks Calculator Agent

**Role**: Calculate and track option Greeks

**Responsibilities**:
- Compute IV using Newton-Raphson
- Calculate Delta, Gamma, Theta, Vega, Rho
- Track IV percentile and IV rank
- Detect IV crush/expansion opportunities
- Model Greek changes over time

**Triggers**:
- Real-time during market hours
- Before any options analysis
- Portfolio risk calculation

**Libraries**: py_vollib, mibian

```python
class GreeksCalculatorAgent:
    """
    Calculates and tracks option Greeks.
    """
    
    async def calculate_greeks(self, strike: Strike) -> Greeks:
        # Get inputs
        spot = await self.get_spot_price(strike.underlying)
        risk_free_rate = 0.07  # 7% in India
        
        # Calculate IV
        iv = self.calculate_iv(
            option_price=strike.ltp,
            spot=spot,
            strike=strike.strike_price,
            dte=strike.days_to_expiry,
            option_type=strike.option_type
        )
        
        # Calculate Greeks
        delta = self.calculate_delta(spot, strike, iv)
        gamma = self.calculate_gamma(spot, strike, iv)
        theta = self.calculate_theta(spot, strike, iv)
        vega = self.calculate_vega(spot, strike, iv)
        
        return Greeks(
            iv=iv,
            iv_percentile=await self.get_iv_percentile(strike.underlying, iv),
            delta=delta,
            gamma=gamma,
            theta=theta,
            vega=vega
        )
```

---

### 11. 📋 Report Generator Agent

**Role**: Create comprehensive analysis reports

**Responsibilities**:
- Compile outputs from all agents
- Generate executive summaries
- Create detailed markdown reports
- Format charts and visualizations
- Produce actionable recommendations
- Generate PDF exports

**Triggers**:
- End of analysis workflow
- User requests report
- Scheduled daily/weekly reports

**Report Types**:
- Scan Results Summary
- Backtest Performance Report
- Portfolio Risk Report
- Market Research Digest
- Strategy Optimization Report

```python
class ReportGeneratorAgent:
    """
    Generates comprehensive reports from agent outputs.
    """
    
    async def generate_report(self, job_id: str, report_type: str):
        # Fetch all agent outputs for this job
        outputs = await self.fetch_job_outputs(job_id)
        
        # Generate report based on type
        if report_type == "BACKTEST":
            report = self.generate_backtest_report(outputs)
        elif report_type == "SCAN":
            report = self.generate_scan_report(outputs)
        elif report_type == "RISK":
            report = self.generate_risk_report(outputs)
        
        # Format as markdown
        markdown = self.format_markdown(report)
        
        # Generate charts
        charts = self.generate_charts(report)
        
        return {
            "markdown": markdown,
            "charts": charts,
            "summary": report.executive_summary
        }
```

---

## Agent Communication Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         USER REQUEST FLOW                                 │
└──────────────────────────────────────────────────────────────────────────┘

User Request                                                     
     │                                                           
     ▼                                                           
┌─────────┐                                                      
│   SQS   │ ◄─── Job Queue                                       
│  Queue  │                                                      
└────┬────┘                                                      
     │                                                           
     ▼                                                           
┌──────────────┐                                                 
│ Orchestrator │                                                 
│    Agent     │                                                 
└──────┬───────┘                                                 
       │                                                         
       ├─────────────────────────────────────────────────────┐   
       │                                                     │   
       ▼                                                     ▼   
┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   Strike    │  │   Greeks    │  │    Risk     │  │    News     │
│   Tagger    │  │ Calculator  │  │   Manager   │  │  Sentiment  │
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                │                │                │      
       └────────────────┴────────────────┴────────────────┘      
                               │                                  
                               ▼                                  
                    ┌─────────────────────┐                       
                    │   Signal Scanner    │                       
                    │   or Backtester     │                       
                    │   or Optimizer      │                       
                    └──────────┬──────────┘                       
                               │                                  
                               ▼                                  
                    ┌─────────────────────┐                       
                    │  Report Generator   │                       
                    └──────────┬──────────┘                       
                               │                                  
                               ▼                                  
                    ┌─────────────────────┐                       
                    │      Database       │                       
                    │   (Job Results)     │                       
                    └──────────┬──────────┘                       
                               │                                  
                               ▼                                  
                         User Response                            


┌──────────────────────────────────────────────────────────────────────────┐
│                      SCHEDULED RESEARCH FLOW                              │
└──────────────────────────────────────────────────────────────────────────┘

EventBridge (Every 2hrs)                                         
     │                                                           
     ▼                                                           
┌─────────────────┐                                              
│ Market Research │ ─── Independent, not orchestrated            
│     Agent       │                                              
└────────┬────────┘                                              
         │                                                       
         ▼                                                       
┌─────────────────┐                                              
│   S3 Vectors    │ ◄─── Knowledge Base                          
│  (Research DB)  │                                              
└─────────────────┘                                              
         │                                                       
         ▼                                                       
   Available for future                                          
   user analysis requests                                        
```

---

## Database Schema for Agent Jobs

```sql
CREATE TABLE agent_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100) NOT NULL,
    job_type VARCHAR(50) NOT NULL,  -- SCAN, BACKTEST, OPTIMIZE, ANALYZE
    status VARCHAR(20) DEFAULT 'pending',  -- pending, processing, completed, failed
    
    -- Request
    request_payload JSONB NOT NULL,
    
    -- Agent outputs (each agent writes to its field)
    tagger_output JSONB,
    greeks_output JSONB,
    risk_output JSONB,
    sentiment_output JSONB,
    scanner_output JSONB,
    backtest_output JSONB,
    optimizer_output JSONB,
    options_analysis_output JSONB,
    report_output JSONB,
    
    -- Summary from orchestrator
    summary JSONB,
    
    -- Metadata
    error_message TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_jobs_user ON agent_jobs(user_id);
CREATE INDEX idx_jobs_status ON agent_jobs(status);
CREATE INDEX idx_jobs_type ON agent_jobs(job_type);
```

---

## AWS Infrastructure

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        AWS INFRASTRUCTURE                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────────────────┐   │
│  │ EventBridge │────▶│   Lambda    │────▶│    SQS Job Queue        │   │
│  │ (Scheduler) │     │ (Scheduler) │     │                         │   │
│  └─────────────┘     └─────────────┘     └───────────┬─────────────┘   │
│                                                      │                  │
│                                                      ▼                  │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │                    LAMBDA FUNCTIONS (Agents)                       │ │
│  ├───────────┬───────────┬───────────┬───────────┬───────────────────┤ │
│  │           │           │           │           │                   │ │
│  │ Orchestr- │ Market    │ Strategy  │ Back-     │ Signal  Options  │ │
│  │ ator      │ Researcher│ Optimizer │ tester    │ Scanner Analyzer │ │
│  │           │           │           │           │                   │ │
│  │ Risk      │ Strike    │ News      │ Greeks    │ Report           │ │
│  │ Manager   │ Tagger    │ Sentiment │ Calculator│ Generator        │ │
│  │           │           │           │           │                   │ │
│  └───────────┴───────────┴───────────┴───────────┴───────────────────┘ │
│                              │                                          │
│              ┌───────────────┼───────────────┐                         │
│              ▼               ▼               ▼                         │
│  ┌─────────────────┐ ┌─────────────┐ ┌─────────────────┐              │
│  │ Aurora Postgres │ │ S3 Vectors  │ │  ElastiCache    │              │
│  │ (Jobs, Users)   │ │ (Knowledge) │ │  Redis (Cache)  │              │
│  └─────────────────┘ └─────────────┘ └─────────────────┘              │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    AWS BEDROCK                                   │   │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────────┐ │   │
│  │  │ Claude Sonnet  │  │  Nova Pro      │  │  Titan Embeddings  │ │   │
│  │  │ (Analysis)     │  │  (Research)    │  │  (Vector Search)   │ │   │
│  │  └────────────────┘  └────────────────┘  └────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Agent Capabilities Matrix

| Agent | AI Model | Lambda Memory | Timeout | Execution Time |
|-------|----------|---------------|---------|----------------|
| Orchestrator | Claude Sonnet | 1024 MB | 5 min | 2-3 min |
| Market Researcher | Claude Sonnet | 2048 MB | 5 min | 30-60 sec |
| Strategy Optimizer | Nova Pro | 3072 MB | 15 min | 5-10 min |
| Backtester | Python only | 3072 MB | 15 min | 2-5 min |
| Signal Scanner | Python only | 2048 MB | 1 min | 10-30 sec |
| Options Analyzer | Claude Sonnet | 1024 MB | 2 min | 20-40 sec |
| Risk Manager | Python + LLM | 1024 MB | 1 min | 10-20 sec |
| Strike Tagger | Claude (Structured) | 512 MB | 30 sec | 5-10 sec |
| News Sentiment | Claude Sonnet | 1024 MB | 2 min | 15-30 sec |
| Greeks Calculator | Python only | 512 MB | 30 sec | 5-10 sec |
| Report Generator | Claude Sonnet | 1024 MB | 2 min | 20-40 sec |

---

## Implementation Phases

### Phase 1: Core Agents (Weeks 17-18)
- Orchestrator Agent
- Strike Tagger Agent
- Greeks Calculator Agent
- Signal Scanner Agent

### Phase 2: Research Agents (Weeks 19-20)
- Market Researcher Agent
- News Sentiment Agent
- Report Generator Agent

### Phase 3: Analysis Agents (Weeks 21-22)
- Backtester Agent
- Strategy Optimizer Agent
- Options Analyzer Agent
- Risk Manager Agent

---

## Example Workflows

### Workflow 1: Full Scan Analysis
```
1. User: "Scan NIFTY for RSI > 60"
2. Orchestrator receives request
3. Parallel: Strike Tagger + Greeks Calculator
4. Signal Scanner runs scan
5. Report Generator creates summary
6. User receives results
```

### Workflow 2: Strategy Backtest
```
1. User: "Backtest my RSI strategy on BankNifty"
2. Orchestrator receives request
3. Backtester runs historical simulation
4. Risk Manager evaluates drawdowns
5. Strategy Optimizer suggests improvements
6. Report Generator creates full report
7. User receives backtest results
```

### Workflow 3: Options Analysis
```
1. User: "Analyze RELIANCE options for bullish trade"
2. Orchestrator receives request
3. Parallel: Greeks Calculator + News Sentiment
4. Options Analyzer suggests strategies
5. Risk Manager validates position size
6. Report Generator creates recommendation
7. User receives trade ideas
```

---

## Key Design Principles

1. **Specialization**: Each agent does one thing exceptionally well
2. **Parallelization**: Independent agents run simultaneously
3. **Isolation**: Agent failures don't crash the system
4. **Observability**: Full tracing with LangFuse
5. **Scalability**: Lambda auto-scales with demand
6. **Cost Efficiency**: Pay only for execution time
7. **Knowledge Sharing**: S3 Vectors enables collective intelligence
