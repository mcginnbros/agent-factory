from strands import tool


@tool
def calculate_compound_interest(
    principal: float,
    rate: float,
    time: float,
    frequency: int = 1
) -> str:
    """
    Calculate compound interest on an investment.
    
    Args:
        principal: The initial amount of money invested (in dollars)
        rate: The annual interest rate (as a percentage, e.g., 5 for 5%)
        time: The time period in years
        frequency: The number of times interest is compounded per year (default: 1)
                  Common values: 1 (annually), 4 (quarterly), 12 (monthly), 365 (daily)
    
    Returns:
        A formatted string with the final amount, total interest earned, and calculation details
    
    Examples:
        - calculate_compound_interest(1000, 5, 10) - $1000 at 5% for 10 years, compounded annually
        - calculate_compound_interest(5000, 4.5, 5, 12) - $5000 at 4.5% for 5 years, compounded monthly
    """
    # Convert rate from percentage to decimal
    r = rate / 100
    
    # Calculate compound interest using formula: A = P(1 + r/n)^(nt)
    # Where: A = final amount, P = principal, r = rate, n = frequency, t = time
    amount = principal * (1 + r / frequency) ** (frequency * time)
    
    # Calculate total interest earned
    interest_earned = amount - principal
    
    # Determine compounding frequency description
    frequency_desc = {
        1: "annually",
        2: "semi-annually",
        4: "quarterly",
        12: "monthly",
        52: "weekly",
        365: "daily"
    }.get(frequency, f"{frequency} times per year")
    
    # Format the result
    result = f"""Compound Interest Calculation
{'=' * 40}
Principal Amount:    ${principal:,.2f}
Annual Interest Rate: {rate}%
Time Period:         {time} year(s)
Compounding:         {frequency_desc}

Final Amount:        ${amount:,.2f}
Total Interest:      ${interest_earned:,.2f}
Effective Gain:      {(interest_earned / principal * 100):.2f}%
"""
    
    return result
