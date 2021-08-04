"""Tools for comparing refinancing options.

Use the `RefinanceOption` class to create options to compare. Use the
`compareRefiOptions` function to determine which is the best option. Set
the function's `silent` argument to `False` to have the results, along
with an explanation, printed to the console.

When comparing refinancing options, you can compare them to your current
mortgage. In this case, make a `RefinanceOption` object to represent
your current mortgage. Set its `payment` attribute to your current
mortgage payment, set the `term` attribute to the number of monthly
payments remaining, and set the `cost` attribute to 0.

Attributes:
    INFLATION (float): The assumed annual inflation rate.

"""

from math import exp, log, ceil
from functools import reduce

INFLATION = 0.03

def applyMonthlyInterest(principal, annualRate):
    """Computes and returns the value of an investment after one month,
    if that investment has the given annual rate of return.

    Args:
        principal (float): The initial value of the investment.
        annualRate (float): The annual rate of return for the
            investment.

    """
    return principal * (1 + annualRate/12)

def calcMonthlyPayment(amountFinanced, interestRate, years, fees=0):
    """Computes and returns the monthly payment when financing the given
    amount at the given annual interest rate for the given number of
    years.

    Args:
        amountFinanced (float): The amount of money that is being
            financed.
        interestRate (float): The annual interest rate.
        years (float): The number of years over which the loan will be
            repaid.
        fees (float): Any additional monthly costs that are required,
            such as taxes and insurance.

    Returns:
        float: The resulting monthly payment.

    """
    # 
    # Let
    # 
    #        t = time (years, t = 0 is start of financing),
    #     y(t) = amount owed at time t,
    #        P = amount financed,
    #        r = annual interest rate of loan,
    #        m = monthly payment, and
    #        T = time at which loan is paid off.
    # 
    # Then y' = ry - 12m and y(0) = P. Solving this initial value
    # problem gives
    # 
    #     y(t) = (P - 12m/r)e^{rt} + 12m/r
    #          = Pe^{rt} - (12m/r)(e^{rt} - 1).
    # 
    # Using y(T) = 0 and solving for m gives
    # 
    #     m = (r/12)Pe^{rT}/(e^{rT} - 1).
    # 
    r = interestRate
    P = amountFinanced
    T = years
    m = (r/12) * P * exp(r*T) / (exp(r*T) - 1)
    return m + fees

def calcNumPayments(amountFinanced, interestRate, monthlyPayment, fees=0):
    """Calculates the number of monthly payments required to pay off a
    loan, given the amount financed, the annual interest rate, and the
    monthly payments.

    Args:
        amountFinanced (float): The amount of money that is being
            financed.
        interestRate (float): The annual interest rate.
        monthlyPayment (float): The amount paid to the lender each
            month.
        fees (float): The amount taken from each monthly payment for
            fees that do not affect the loan amount, such as taxes and
            insurance.

    Returns:
        float: The number of monthly payments required.

    """
    # 
    # We again use
    # 
    #     0 = (P - 12m/r)e^{rT} + 12m/r,
    # 
    # where all the variables have the same meaning as in the comments
    # for `calcMonthlyPayment`. This time we solve for T:
    # 
    #     T = (1/r)log(12m/(12m - rP)).
    # 
    r = interestRate
    m = monthlyPayment - fees
    P = amountFinanced
    T = (1/r) * log(12*m / (12*m - r*P))
    return 12 * T

def simulate(
    refiOption, monthlyCash, investmentGrowthRate, horizon, silent=True
):
    """Simulates the paying off of a mortgage while also investing in an
    external investment (such as a retirement fund) for a given number
    of months. Returns the present value of your final wealth at the end
    of the simulation.

    (This final wealth includes only the value of the investment, and
    not the home you are refinancing, whose value is assumed to be
    independent of which refinancing option you choose).

    Args:
        refiOption (RefinanceOption): The refinancing option to use in
            the simulation.
        monthlyCash (float): The amount of cash available each month to
            put toward the mortgage and/or the external investment.
        investmentGrowthRate (float or (list of float)): The annual
            growth rate of the external investment. If a list is
            provided, then the j-th value represents the annual growth
            rate during the j-th month of the simulation.
        horizon (int): The number of months to include in the
            simulation.
        silent (bool): Set to `False` to print the results of the
            simulation, with an explanation, to the console.

    Returns:
        float: The present value of your wealth in the investment at the
            end of the simulation.

    Raises:
        ValueError: If `investmentGrowthRate` is a list whose length is
            less than `horizon`, or if `monthlyCash` is less than the
            monthly payment of the given refinancing option.

    """
    rates = investmentGrowthRate
    if type(rates) == type([]):
        if len(rates) < horizon:
            raise ValueError(
                'List of investment growth rates not long enough to simulate '
                + str(horizon) + ' months'
            )
    else:
        rates = [investmentGrowthRate] * horizon
    if monthlyCash < refiOption.payment:
        raise ValueError(
            "You don't have enough monthly cash to make the mortgage payments"
        )
        return

    terminalWealth = 0
    for month in range(horizon):
        payment = refiOption.payment if month < refiOption.term else 0
        if month == 0:
            payment += refiOption.cost
        netCash = monthlyCash - payment
        terminalWealth += reduce(
            applyMonthlyInterest, rates[month: horizon], netCash
        )
    presentValue = terminalWealth * exp(-INFLATION * horizon/12)

    if not silent:
        cost = '{:,.2f}'.format(refiOption.cost)
        term = str(refiOption.term)
        remaining = str(horizon - refiOption.term)
        payment = '{:,.2f}'.format(refiOption.payment)
        cash = '{:,.2f}'.format(monthlyCash)
        surplus = '{:,.2f}'.format(monthlyCash - refiOption.payment)
        wealth = '{:,.2f}'.format(terminalWealth)
        value = '{:,.2f}'.format(presentValue)
        print(
            'Make an initial payment of $' + cost + '\n' +
            'First ' + term + ' months:\n' +
            '    Spend $' + payment + ' on a mortgage payment.\n' +
            '    Put $' + surplus + ' in the security.\n' +
            'Last ' + remaining + ' months:\n' +
            '    Spend $0.00 on a mortgage payment.\n' +
            '    Put $' + cash + ' in the security.\n' +
            'After ' + str(horizon) + ' months, '
                + 'you have $' + wealth + ' in the security.\n' +
            "In today's dollars, that's $" + value + '.'
        )

    return presentValue

def compareRefiOptions(investmentGrowthRate, *refiOptions, silent=True):
    """Compares the given refinancing options under the assumption that
    any excess money will be put into an external investment with the
    given growth rate. Assumes that investing will occur for a number of
    months given by the maximum term of the provided refinancing
    options. For each option, computes the present value of your final
    wealth in the external investment. Returns the option that produces
    the greatest present value.

    Args:
        investmentGrowthRate (float or (list of float)): The annual
            growth rate of the external investment. If a list is
            provided, then the j-th value represents the annual growth
            rate during the j-th month of the comparison.
        refiOptions (list of RefinanceOption): The refinancing options
            to compare.
        silent (bool): Set to `False` to print the results of the
            comparison, with an explanation, to the console.

    Returns:
        RefinanceOption: The option that produces the greatest present
            value

    """
    monthlyCash = max(option.payment for option in refiOptions)
    horizon = max(option.term for option in refiOptions)
    if not silent:
        cash = '{:,.2f}'.format(monthlyCash)
        print(
            '\nSuppose you have $' + cash + ' available each '
                + 'month for the next ' + str(horizon) + ' months,\n' +
            'and access to a security yielding the annual return you provided'
        )
    maxVal = 0
    maxOption = None
    for option in refiOptions:
        if not silent:
            print('\nSCENARIO ' + str(refiOptions.index(option) + 1))
            print('-' * 10 + '\n')
        val = simulate(
            option, monthlyCash, investmentGrowthRate, horizon, silent
        )
        if val > maxVal:
            maxOption = option
    return maxOption

class RefinanceOption():
    """A refinancing option to evaluate.

    Attributes:
        cost (float): The initial out-of-pocket cost to refinance under
            this option.
        payment (float): The monthly payment you would have under this
            option.
        term (int): The number of monthly payments you would need to
            make under this option.

    """

    def __init__(self, payment, term, cost=0):
        self.payment = payment
        self.term = term
        self.cost = cost
