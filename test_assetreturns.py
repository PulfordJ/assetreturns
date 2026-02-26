from assetreturns import calculateSDLT, generatePropertyForecast, InterestOnlyMortgage, EarlyRepaymentMortgage
from assetreturns import calculateCapitalGains
from assetreturns import RepaymentMortgage
from assetreturns import TaxDeductibleMortgage
from assetreturns import Property
from assetreturns import mortgageFactory
from assetreturns import HLStock
interest_rate = 0.0187
interest_rate = 0.0359
def test_calculateSDLT():
    # Standard property tests
    assert calculateSDLT(False, 100000) == 0
    assert calculateSDLT(False, 200000) == 1500  # (200k-125k) * 2%

    # Second property tests (with 5% surcharge)
    assert calculateSDLT(True, 100000) == 5000  # 100k * 5%
    assert calculateSDLT(True, 300000) == 20000  # 125k*5% + 125k*7% + 50k*10%

    # First-time buyer tests
    assert calculateSDLT(False, 250000, is_first_time_buyer=True) == 0
    assert calculateSDLT(False, 300000, is_first_time_buyer=True) == 0
    assert calculateSDLT(False, 400000, is_first_time_buyer=True) == 5000  # (400k-300k) * 5%
    assert calculateSDLT(False, 500000, is_first_time_buyer=True) == 10000  # (500k-300k) * 5%

    # First-time buyer doesn't apply above £500k - uses standard rates
    assert calculateSDLT(False, 600000, is_first_time_buyer=True) == calculateSDLT(False, 600000)

    # First-time buyer relief doesn't apply to second properties
    assert calculateSDLT(True, 300000, is_first_time_buyer=True) == calculateSDLT(True, 300000)

def test_RepaymentMortgage():
    mortgage = RepaymentMortgage(75000, 25, interest_rate)
    assert mortgage.total_interest(25) == 38029.8398044053
    assert RepaymentMortgage(372000, 25, interest_rate).total_interest(25) == 188628.00542985174
    assert RepaymentMortgage(372000, 25, interest_rate).total_interest(5) == 61429.124641477014

def test_taxdeductiblemortgage():
    assert TaxDeductibleMortgage(0.2, RepaymentMortgage, 372000, 25, interest_rate).total_interest(25) == 150902.40434388138

def test_calculateCapitalGains():
    assert calculateCapitalGains(True, 12000) == 0
    assert calculateCapitalGains(True, 12000) == 0
    assert calculateCapitalGains(False, 20000) == 1540
    assert calculateCapitalGains(True, 20000) == 2156

def test_mortgage_factory():
    assert mortgageFactory(TaxDeductibleMortgage, 751,  property_price=100000, tax_rate=0.2, ltv_percentage=1, MortgageClassToDecorate=RepaymentMortgage, length=25, interest_rate=0.03).monthly_installment == 472.1062585741442

def test_interest_only_mortgage():
    assert InterestOnlyMortgage(100000, length=25, interest_rate=0.03).monthly_installment == 250


def test_property():
    property_forecast = Property(True, 100000, TaxDeductibleMortgage(0.2, RepaymentMortgage, 75000, 25, interest_rate), monthly_gross_rental=750, rental_tax=0.45, months_occupied_out_of_12=10, agency_percentage=.2)
    assert property_forecast.calculate_profits(5) == 2217.0766707295206

def test_property_generator_and_property():
    property_forecast = generatePropertyForecast(True, 100000, monthly_gross_rental=750, rental_tax=0.45,
                                        months_occupied_out_of_12=10,
                                        agency_percentage=.2, MortgageClass=TaxDeductibleMortgage, ltv_percentage=.75,
                                        MortgageClassToDecorate=RepaymentMortgage, tax_rate=0.2, length=12,
                                        interest_rate=0.03)

    # Updated values due to SDLT surcharge change from 3% to 5% (£2000 difference)
    assert property_forecast.initial_equity_cost == 25000.144439697266
    assert property_forecast.nominal_return_on_investment(25, 0, 0) == 115492.09528851448
    assert property_forecast.percentage_return_on_investment(25, 0, 0) == 4.619657121065537
    assert property_forecast.annual_percentage_return_on_investment(25, 0, 0) == 0.07149066741581467

def test_hlstock():
    hl_stock = HLStock(200000, 21.73)
    assert hl_stock.nominal_return_on_investment(1, 0, 0) == 4667.777523561876

def test_hlstock_future_deposits():
    hl_stock = HLStock(100000, 20, [1000])
    assert hl_stock.nominal_return_on_investment(1, 0, 0) == 4667.777523561876+500

def test_percentage_yoy_negative_case():
    hl_stock = HLStock(200000, -10)
    assert hl_stock.nominal_return_on_investment(1, 0, 0) == 11463.911900000006
    assert hl_stock.percentage_return_on_investment(1, 0, 0) == 0.057319559500000034
    assert hl_stock.percentage_return_on_investment(2, 0, 0) == 0.12931955950000004
    assert hl_stock.percentage_return_on_investment(10, 0, 0) == -0.6740020003999999
    assert hl_stock.annual_percentage_return_on_investment(10, 0, 0) == -0.6740020003999999

def test_earlyrepayment_on_repaymentmortgage():
    # The line below needs work
    # TODO do we track the month that starts the year for max repayment? The approximation seems decent enough
    interest_rate = 0.01
    assert RepaymentMortgage(372000, 25, interest_rate,{1*12: 0.1, 2*12: 0.1, 3*12: 0.1, 3*12: 0.1, 4*12: 1}).total_interest(25) == 11797.1536295663

def test_total_principle_paid():
    interest_rate = 0.01
    # Rounding error but it's insignificant
    assert RepaymentMortgage(372000, 25, interest_rate,
                             {1 * 12: 0.1, 2 * 12: 0.1, 3 * 12: 0.1, 3 * 12: 0.1, 4 * 12: 1}).total_payments(
        25) == 383797.1536295662
    assert RepaymentMortgage(372000, 25, interest_rate, {1 * 12: 0.1, 2 * 12: 0.1, 3 * 12: 0.1, 3 * 12: 0.1, 4 * 12: 1}).total_principle_paid(25) == 371999.9999999999
    interest_rate = 0.02
    repayment_mortgage =  RepaymentMortgage(540000, 25, interest_rate,
                             {1 * 12: 0.1, 2 * 12: 0.1, 3 * 12: 0.1, 4 * 12: 0.1, 5 * 12: 1})
    assert repayment_mortgage.total_payments(25) == 579974


#TODO build factory that generates mortgage based on monthly_gross_rental, and property value, and uses it to create a property.

#print(Mortgage(75000, 25, 0.02).total_interest)
#taxDeductibleMortgage = TaxDeductibleMortgage(75000, 25, 0.02, 0.2)
#print(taxDeductibleMortgage.total_interest)
#property = Property(True, 100000, taxDeductibleMortgage, monthly_gross_rental=800, rental_tax=0.45, months_occupied_out_of_12=8, agency_percentage=0.2) 
