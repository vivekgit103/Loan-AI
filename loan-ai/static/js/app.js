/**
 * TrustScore AI / LoanIQ - Client-Side Underwriting & Interactive Financial Diagnostics
 * Vanilla JavaScript implementation for:
 * 1. Live EMI calculations, FOIR diagnostics, CIBIL calibration
 * 2. Searchable applications table filter
 * 3. Custom CSS Bar Chart rendered into #chart-area (No chart libraries)
 */

document.addEventListener("DOMContentLoaded", () => {
  try {
    initLiveLoanCalculator();
    initApplicationsTableFilter();
    initMonthlyBarChart();
  } catch (err) {
    console.error("Initialization error:", err);
  }
});

/**
 * ------------------------------------------------------------------------------
 * 1. Custom CSS Bar Chart for #chart-area (No Chart Libraries)
 * ------------------------------------------------------------------------------
 * Fetches monthly counts from /api/stats (last 6 months: approved, review, rejected).
 * Renders 3 bars per month:
 *   - Green #10b981 (Approved)
 *   - Blue #0d6efd (Review)
 *   - Orange #f97316 (Rejected)
 * Features:
 *   - 12px border radius
 *   - Animated from 0 to full proportional height with transition-all duration-700 ease-in-out
 *   - Highest month highlighted with floating white shadow-md tooltip badge ("📈 X apps")
 *   - On hover of any bar: dark #111827 tooltip with white text ("Approved: 18")
 *   - Legend & Y-axis with 4 dashed grid lines
 *   - Graceful fallback for empty data
 */
function initMonthlyBarChart() {
  const chartContainer = document.getElementById("chart-area");
  if (!chartContainer) return;

  // Global hover popover element (single singleton)
  let popover = document.getElementById("chartHoverPopover");
  if (!popover) {
    popover = document.createElement("div");
    popover.id = "chartHoverPopover";
    popover.className = "chart-hover-popover";
    document.body.appendChild(popover);
  }

  fetch("/api/stats")
    .then((res) => {
      if (!res.ok) throw new Error("Network error fetching stats");
      return res.json();
    })
    .then((payload) => {
      const stats = payload.data || {};
      const monthlyData = payload.monthly_counts || stats.monthly_counts || [];
      renderBarChart(chartContainer, monthlyData, popover);
    })
    .catch((err) => {
      console.warn("Falling back to local chart data:", err);
      // Fallback sample data if API is unavailable
      const fallbackMonths = [
        { month: "2024-06", display_month: "Jun", approved: 3, review: 1, rejected: 1, total: 5 },
        { month: "2024-07", display_month: "Jul", approved: 5, review: 2, rejected: 1, total: 8 },
        { month: "2024-08", display_month: "Aug", approved: 7, review: 2, rejected: 2, total: 11 },
        { month: "2024-09", display_month: "Sep", approved: 9, review: 3, rejected: 2, total: 14 },
        { month: "2024-10", display_month: "Oct", approved: 12, review: 4, rejected: 3, total: 19 },
        { month: "2024-11", display_month: "Nov", approved: 15, review: 5, rejected: 2, total: 22 }
      ];
      renderBarChart(chartContainer, fallbackMonths, popover);
    });
}

function renderBarChart(container, months, popover) {
  // If no data
  if (!months || months.length === 0) {
    container.innerHTML = `
      <div class="flex items-center justify-between pb-4 border-b border-[#f3f4f6]">
        <div>
          <h3 class="text-sm font-bold text-[#1e293b]">Underwriting Activity & Monthly Decision Trends</h3>
          <p class="text-[11px] text-[#64748b]">Monthly loan volume breakdown (Approved, Review, Rejected)</p>
        </div>
      </div>
      <div class="flex-1 flex flex-col items-center justify-center p-8 text-center text-[#64748b]">
        <svg class="w-12 h-12 text-slate-300 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
        <p class="text-xs font-bold text-[#1e293b]">No Monthly Pipeline Data Yet</p>
        <p class="text-[11px] text-[#64748b] mt-0.5">Submit new applications to view monthly underwriting trends.</p>
      </div>
    `;
    return;
  }

  // Calculate highest volume month & highest single bar value
  let maxSingleVal = 1;
  let highestMonthIndex = -1;
  let highestMonthTotal = -1;

  months.forEach((m, idx) => {
    const app = parseInt(m.approved || 0);
    const rev = parseInt(m.review || 0);
    const rej = parseInt(m.rejected || 0);
    const tot = parseInt(m.total || (app + rev + rej));

    if (app > maxSingleVal) maxSingleVal = app;
    if (rev > maxSingleVal) maxSingleVal = rev;
    if (rej > maxSingleVal) maxSingleVal = rej;

    if (tot > highestMonthTotal) {
      highestMonthTotal = tot;
      highestMonthIndex = idx;
    }
  });

  // Round maxSingleVal up to comfortable nice number for 4 grid lines
  let yMax = Math.max(4, Math.ceil(maxSingleVal / 4) * 4);
  const step = yMax / 4;
  const yLabels = [yMax, yMax - step, yMax - (step * 2), step, 0];

  // Build HTML Shell with Legend, Header, and Chart Canvas
  container.innerHTML = `
    <!-- Chart Header & Interactive Legend -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-[#f3f4f6] gap-3">
      <div>
        <h3 class="text-sm font-bold text-[#1e293b]">Underwriting Activity & Monthly Decision Trends</h3>
        <p class="text-[11px] text-[#64748b]">Monthly volume breakdown: Approved, Review, and Rejected</p>
      </div>

      <!-- Legend -->
      <div class="flex items-center space-x-3 text-[11px]">
        <div class="inline-flex items-center text-[#10b981] font-bold">
          <span class="w-2.5 h-2.5 rounded-full bg-[#10b981] mr-1.5 shadow-xs"></span>
          Approved
        </div>
        <div class="inline-flex items-center text-[#0d6efd] font-bold">
          <span class="w-2.5 h-2.5 rounded-full bg-[#0d6efd] mr-1.5 shadow-xs"></span>
          Review
        </div>
        <div class="inline-flex items-center text-[#f97316] font-bold">
          <span class="w-2.5 h-2.5 rounded-full bg-[#f97316] mr-1.5 shadow-xs"></span>
          Rejected
        </div>
      </div>
    </div>

    <!-- Chart Plot Area with Y-Axis Grid Lines -->
    <div class="relative flex-1 mt-6 pt-6 pb-2 min-h-[220px] flex">
      
      <!-- Y-Axis Grid Labels (Left) -->
      <div class="w-8 shrink-0 flex flex-col justify-between text-right pr-2 text-[10px] font-semibold text-[#64748b] select-none h-44">
        <span>${yLabels[0]}</span>
        <span>${yLabels[1]}</span>
        <span>${yLabels[2]}</span>
        <span>${yLabels[3]}</span>
        <span>0</span>
      </div>

      <!-- Bars Canvas Area -->
      <div class="relative flex-1 h-44 flex items-end">
        
        <!-- 4 Dashed Grid Lines (Top to Bottom) -->
        <div class="chart-grid-line" style="bottom: 100%;"></div>
        <div class="chart-grid-line" style="bottom: 75%;"></div>
        <div class="chart-grid-line" style="bottom: 50%;"></div>
        <div class="chart-grid-line" style="bottom: 25%;"></div>
        <div class="chart-grid-line border-t border-slate-200" style="bottom: 0%;"></div>

        <!-- Month Groups Container -->
        <div class="w-full h-full flex justify-around items-end z-10 px-2">
          ${months.map((m, idx) => {
            const app = parseInt(m.approved || 0);
            const rev = parseInt(m.review || 0);
            const rej = parseInt(m.rejected || 0);
            const tot = parseInt(m.total || (app + rev + rej));

            // Proportional heights in percentage (0 to 100)
            const appPct = Math.round((app / yMax) * 100);
            const revPct = Math.round((rev / yMax) * 100);
            const rejPct = Math.round((rej / yMax) * 100);

            // Month display formatting
            let monthLabel = m.display_month || m.month || `M${idx + 1}`;
            if (monthLabel.includes(" ")) {
              monthLabel = monthLabel.split(" ")[0]; // "Jun"
            }

            const isHighest = (idx === highestMonthIndex && tot > 0);

            return `
              <div class="relative flex-1 max-w-[80px] h-full flex flex-col justify-end items-center group">
                
                <!-- Floating White Badge for Highest Month -->
                ${isHighest ? `
                  <div class="chart-tooltip-badge animate-bounce">
                    📈 ${tot} apps
                  </div>
                ` : ''}

                <!-- 3 Bars Group (Approved, Review, Rejected) -->
                <div class="w-full flex justify-center items-end gap-1.5 h-full pb-1">
                  
                  <!-- Bar 1: Approved - Green #10b981 -->
                  <div class="chart-bar w-2.5 sm:w-3.5 bg-[#10b981] transition-all duration-700 ease-in-out"
                       data-target-height="${appPct}%"
                       data-tooltip="Approved: ${app}"
                       style="height: 0%;"></div>

                  <!-- Bar 2: Review - Blue #0d6efd -->
                  <div class="chart-bar w-2.5 sm:w-3.5 bg-[#0d6efd] transition-all duration-700 ease-in-out"
                       data-target-height="${revPct}%"
                       data-tooltip="Review: ${rev}"
                       style="height: 0%;"></div>

                  <!-- Bar 3: Rejected - Orange #f97316 -->
                  <div class="chart-bar w-2.5 sm:w-3.5 bg-[#f97316] transition-all duration-700 ease-in-out"
                       data-target-height="${rejPct}%"
                       data-tooltip="Rejected: ${rej}"
                       style="height: 0%;"></div>

                </div>

                <!-- Month Label Below Base -->
                <span class="text-[10px] font-bold text-[#64748b] mt-1 select-none">
                  ${monthLabel}
                </span>

              </div>
            `;
          }).join('')}
        </div>

      </div>

    </div>

    <!-- Chart Footer Caption -->
    <div class="pt-3 border-t border-[#f3f4f6] flex flex-col sm:flex-row items-center justify-between text-[11px] text-[#64748b] gap-1">
      <span>Highest Velocity: <strong class="text-[#1e293b]">${highestMonthTotal > 0 ? `${highestMonthTotal} applications` : 'N/A'}</strong> in top cycle</span>
      <span class="text-[#0d6efd] font-semibold">Hover bars for granular tallies</span>
    </div>
  `;

  // Animate bars from height 0% to proportional target heights after slight delay
  setTimeout(() => {
    const bars = container.querySelectorAll(".chart-bar");
    bars.forEach((bar) => {
      const target = bar.getAttribute("data-target-height") || "0%";
      bar.style.height = target;
    });
  }, 100);

  // Attach Dark Tooltip Hover Events
  attachChartTooltips(container, popover);
}

function attachChartTooltips(container, popover) {
  const bars = container.querySelectorAll(".chart-bar");

  bars.forEach((bar) => {
    bar.addEventListener("mouseenter", (e) => {
      const tipText = bar.getAttribute("data-tooltip") || "";
      if (!tipText) return;

      popover.textContent = tipText;
      popover.style.opacity = "1";

      const rect = bar.getBoundingClientRect();
      const popWidth = popover.offsetWidth;
      const leftPos = rect.left + (rect.width / 2) - (popWidth / 2);
      const topPos = rect.top - 36;

      popover.style.left = `${Math.max(10, leftPos)}px`;
      popover.style.top = `${Math.max(10, topPos)}px`;
    });

    bar.addEventListener("mousemove", (e) => {
      const rect = bar.getBoundingClientRect();
      const popWidth = popover.offsetWidth;
      const leftPos = rect.left + (rect.width / 2) - (popWidth / 2);
      const topPos = rect.top - 36;

      popover.style.left = `${Math.max(10, leftPos)}px`;
      popover.style.top = `${Math.max(10, topPos)}px`;
    });

    bar.addEventListener("mouseleave", () => {
      popover.style.opacity = "0";
    });
  });
}

/**
 * ------------------------------------------------------------------------------
 * 2. Live Underwriting & EMI Calculator for apply.html
 * ------------------------------------------------------------------------------
 */
function initLiveLoanCalculator() {
  const loanForm = document.getElementById("loanForm");
  if (!loanForm) return;

  const monthlyIncomeEl = document.getElementById("monthly_income");
  const existingEmiEl = document.getElementById("existing_emi");
  const creditScoreSlider = document.getElementById("credit_score");
  const creditScoreInput = document.getElementById("credit_score_input");
  const cibilBadge = document.getElementById("cibilBadge");
  const creditUtilSlider = document.getElementById("credit_utilization");
  const creditUtilVal = document.getElementById("utilizationVal");
  const loanTypeSelect = document.getElementById("loan_type");
  const loanAmountEl = document.getElementById("loan_amount");
  const tenureSelect = document.getElementById("tenure_months");

  const previewEmi = document.getElementById("previewEmi");
  const previewRate = document.getElementById("previewRate");
  const previewFoirText = document.getElementById("previewFoirText");
  const foirProgressBar = document.getElementById("foirProgressBar");
  const previewMaxEligible = document.getElementById("previewMaxEligible");

  // Sync CIBIL Slider and Numeric Box
  function syncCibil(val) {
    val = Math.min(900, Math.max(300, parseInt(val) || 650));
    creditScoreSlider.value = val;
    creditScoreInput.value = val;

    if (val >= 750) {
      cibilBadge.className = "text-xs font-extrabold px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800";
      cibilBadge.textContent = `Excellent (${val})`;
    } else if (val >= 650) {
      cibilBadge.className = "text-xs font-extrabold px-2.5 py-0.5 rounded-full bg-sky-100 text-sky-800";
      cibilBadge.textContent = `Good (${val})`;
    } else if (val >= 550) {
      cibilBadge.className = "text-xs font-extrabold px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-800";
      cibilBadge.textContent = `Fair (${val})`;
    } else {
      cibilBadge.className = "text-xs font-extrabold px-2.5 py-0.5 rounded-full bg-rose-100 text-rose-800";
      cibilBadge.textContent = `Subprime (${val})`;
    }
  }

  if (creditScoreSlider && creditScoreInput) {
    creditScoreSlider.addEventListener("input", (e) => {
      syncCibil(e.target.value);
      recalculateDiagnostics();
    });

    creditScoreInput.addEventListener("input", (e) => {
      syncCibil(e.target.value);
      recalculateDiagnostics();
    });
  }

  if (creditUtilSlider && creditUtilVal) {
    creditUtilSlider.addEventListener("input", (e) => {
      creditUtilVal.textContent = `${e.target.value}%`;
    });
  }

  // Attach recalculate listeners to all relevant inputs
  [monthlyIncomeEl, existingEmiEl, loanTypeSelect, loanAmountEl, tenureSelect].forEach((el) => {
    if (el) {
      el.addEventListener("input", recalculateDiagnostics);
      el.addEventListener("change", recalculateDiagnostics);
    }
  });

  function getBenchmarkRate(type, score) {
    const baseRates = {
      Home: 8.5,
      Personal: 11.5,
      Auto: 9.5,
      Education: 9.0,
      Business: 13.5,
      Gold: 8.9
    };
    let base = baseRates[type] || 11.5;
    let spread = 0.0;

    if (score >= 780) spread = -0.25;
    else if (score >= 720) spread = 0.0;
    else if (score >= 650) spread = 1.25;
    else if (score >= 600) spread = 2.5;
    else spread = 3.5;

    return Math.max(7.5, base + spread);
  }

  function recalculateDiagnostics() {
    const income = Math.max(0, parseFloat(monthlyIncomeEl?.value) || 0);
    const existingEmi = Math.max(0, parseFloat(existingEmiEl?.value) || 0);
    const score = parseInt(creditScoreSlider?.value || 650);
    const loanType = loanTypeSelect?.value || "Personal";
    const amount = Math.max(0, parseFloat(loanAmountEl?.value) || 0);
    const tenureMonths = Math.max(6, parseInt(tenureSelect?.value || 36));

    const rate = getBenchmarkRate(loanType, score);
    if (previewRate) previewRate.textContent = `${rate.toFixed(2)}%`;

    // Standard reducing balance formula
    const monthlyRate = rate / (12 * 100);
    let newEmi = 0.0;
    if (monthlyRate > 0 && amount > 0) {
      const pow = Math.pow(1 + monthlyRate, tenureMonths);
      newEmi = (amount * monthlyRate * pow) / (pow - 1);
    }
    if (previewEmi) previewEmi.textContent = `₹${Math.round(newEmi).toLocaleString("en-IN")}`;

    // FOIR
    const totalObligations = existingEmi + newEmi;
    let foir = 0.0;
    if (income > 0) {
      foir = (totalObligations / income) * 100;
    }
    const roundedFoir = Math.min(100, Math.max(0, foir));

    if (previewFoirText) previewFoirText.textContent = `${foir.toFixed(1)}%`;
    if (foirProgressBar) {
      foirProgressBar.style.width = `${roundedFoir}%`;
      foirProgressBar.className = "h-full rounded-full transition-all duration-300 ";
      if (foir <= 40) {
        foirProgressBar.classList.add("bg-emerald-500");
      } else if (foir <= 50) {
        foirProgressBar.classList.add("bg-sky-500");
      } else if (foir <= 65) {
        foirProgressBar.classList.add("bg-amber-500");
      } else {
        foirProgressBar.classList.add("bg-rose-500");
      }
    }

    // Maximum Borrowing Capacity (Reverse solved from 50% FOIR cap)
    const maxPermissibleTotalEmi = income * 0.50;
    const maxPermissibleNewEmi = Math.max(0, maxPermissibleTotalEmi - existingEmi);
    let maxLoanAmount = 0.0;

    if (monthlyRate > 0 && maxPermissibleNewEmi > 0) {
      const pow = Math.pow(1 + monthlyRate, tenureMonths);
      maxLoanAmount = (maxPermissibleNewEmi * (pow - 1)) / (monthlyRate * pow);
    }
    if (previewMaxEligible) {
      previewMaxEligible.textContent = `₹${Math.round(maxLoanAmount).toLocaleString("en-IN")}`;
    }
  }

  // Initial calculation on page load
  recalculateDiagnostics();
}

/**
 * ------------------------------------------------------------------------------
 * 3. Search & Decision Filtering for Applications Registry (/applications)
 * ------------------------------------------------------------------------------
 */
function initApplicationsTableFilter() {
  const table = document.getElementById("applicationsTable");
  if (!table) return;

  const searchInput = document.getElementById("tableSearch");
  const filterBtns = document.querySelectorAll(".filter-btn");
  const tableRows = table.querySelectorAll("tbody tr");
  const noResultsState = document.getElementById("noResultsState");

  let currentFilter = "all";
  let searchQuery = "";

  function applyFilters() {
    let visibleCount = 0;

    tableRows.forEach((row) => {
      const decision = row.getAttribute("data-decision");
      const searchContent = row.getAttribute("data-search") || "";

      const matchesFilter = (currentFilter === "all" || decision === currentFilter);
      const matchesSearch = !searchQuery || searchContent.includes(searchQuery);

      if (matchesFilter && matchesSearch) {
        row.style.display = "";
        visibleCount++;
      } else {
        row.style.display = "none";
      }
    });

    if (noResultsState) {
      noResultsState.classList.toggle("hidden", visibleCount > 0);
    }
  }

  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      searchQuery = e.target.value.toLowerCase().trim();
      applyFilters();
    });
  }

  filterBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      filterBtns.forEach((b) => {
        b.classList.remove("active", "bg-sky-50", "text-sky-700");
        b.classList.add("text-slate-600");
      });

      btn.classList.add("active", "bg-sky-50", "text-sky-700");
      btn.classList.remove("text-slate-600");

      currentFilter = btn.getAttribute("data-filter") || "all";
      applyFilters();
    });
  });
}
