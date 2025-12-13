import numpy as np
import numpy_financial
import pandas as pd
from abc import ABC, abstractmethod
from tabulate import tabulate
import altair as alt


def calculateSDLT(second_property, property_value):
    rates = [0.00, .02, 0.05, 0.10, 0.12]
    thresholds = [125000, 250000, 925000, 1500000, 10000000]
    total_tax = 0
    remaining_taxable = property_value
    if second_property:
        rates = [rate + 0.03 for rate in rates]
    for i in range(len(thresholds) - 1, -1, -1):
        threshold = thresholds[i]
        rate = rates[i]
        if i != 0:
            lower_threshold = thresholds[i - 1]
            if lower_threshold >= remaining_taxable:
                continue
            threshold_taxable = remaining_taxable - lower_threshold
            remaining_taxable = lower_threshold
        else:
            threshold_taxable = remaining_taxable
        threshold_tax = threshold_taxable * rate
        total_tax += threshold_tax
    return total_tax


class Mortgage(ABC):

    @property
    def principle(self):
        return self._principle

    def __total_repayments(self, years):
        return self.payment_table["Payment"][0:years * 12].sum()

    def total_payments(self, years):
        return self.payment_table["Payment"][0:years * 12].sum()

    def total_principle_paid(self, years):
        return self.__total_repayments(years) - self.total_interest(years)

    def total_interest(self, years):
        # TODO calculate interest total
        return self.payment_table["Interest"][0:years * 12].sum()

    def total_fees(self, years):
        return self.total_interest(years) + 1000


class AbstractMortgage(Mortgage):
    """
    Mortgage with some generation logic based on interest rates and monthly repayments.
    A Repayment or InterestOnly mortgage sublcass can then provide appropriate interest rates
    and monthly repayments.
    """
    def _render_mortgage_payment_table(self):
        pass

    def __init__(self, principle, length, periodic_interest_rate, monthly_installment, early_repayment_months_and_amount={}):
        self._principle = principle
        payment_months = length * 12

        self.monthly_installment = monthly_installment
        self.payment_table = pd.DataFrame(index=np.arange(0, payment_months),
                                          columns=["Principle", "Interest", "Payment", "Early Repayment"])
        self.payment_table.loc[0] = [principle, periodic_interest_rate * principle, self.monthly_installment, 0]
        # Default this column to 0
        self.payment_table["Early Repayment"].values[:] = 0
        for i in range(1, payment_months):
            previous_row = self.payment_table.loc[i - 1]
            previous_principle = previous_row["Principle"]
            previous_interest = previous_row["Interest"]
            previous_payment = previous_row["Payment"]
            current_row = self.payment_table.loc[i]
            current_row["Principle"] = previous_principle + previous_interest - previous_payment
            current_row["Interest"] = self.payment_table.loc[i]["Principle"] * periodic_interest_rate
            month = i +1
            if month in early_repayment_months_and_amount:
                principle_percentage_to_repay = early_repayment_months_and_amount[month]
                start_of_year_index = (month / 12) * 12-1
                start_of_year_row = self.payment_table.loc[start_of_year_index]
                current_row["Early Repayment"] =  principle_percentage_to_repay * start_of_year_row["Principle"]

            current_row["Payment"] = min(self.monthly_installment+current_row["Early Repayment"], current_row["Principle"] + current_row["Interest"])

        # TODO simplify this, last row should just be remaining balance, only line 81 seems to need to stay
        last_row = self.payment_table.loc[payment_months - 1]
        last_row["Payment"] = last_row["Principle"] + last_row["Interest"]
        # self.payment_table = pd.concat([self.payment_table, pd.Series([principle, 1, 0])])
        # self.payment_table = self.payment_table.append(pd.DataFrame([principle, 1, 0], ))
        # TODO create dataframe for interest generation? Or use algorithm


class InterestOnlyMortgage(AbstractMortgage):
    def __init__(self, principle, length, interest_rate):
        # Thought this would be the same as RepaymentMortgages but comparison calculators tell me it seems to be calculated
        # interest_rate / 12!
        periodic_interest_rate = interest_rate / 12
        monthly_installment = principle * periodic_interest_rate
        super().__init__(principle, length, periodic_interest_rate, monthly_installment)

    def total_fees(self, years):
        return self.total_interest(years) + 2000


class RepaymentMortgage(AbstractMortgage):
    def __init__(self, principle, length, interest_rate, early_repayment_months_and_amount={}):
        payment_months = length * 12
        periodic_interest_rate = (1 + interest_rate) ** (1 / 12) - 1

        monthly_installment = 1 * numpy_financial.pmt(periodic_interest_rate, payment_months, principle) * -1
        super().__init__(principle, length, periodic_interest_rate, monthly_installment, early_repayment_months_and_amount)

    @property
    def principle(self):
        return self._principle

    def total_interest(self, years):
        # TODO calculate interest total
        return self.payment_table["Interest"][0:years * 12].sum()

    def total_fees(self, years):
        return self.total_interest(years) + 1000


interest_rate = 0.0187
interest_rate = 0.0359


# print(Mortgage(372000, 25, interest_rate).payment_table)
# mortgage = Mortgage(75000, 25, interest_rate)
# print(mortgage.payment_table)

class TaxDeductibleMortgage(Mortgage):
    def __init__(self, tax_rate, MortgageClassToDecorate, *mortgage_class_args, **mortgage_class_kwargs):
        super().__init__()
        self.wrapped_mortgage = MortgageClassToDecorate(*mortgage_class_args, **mortgage_class_kwargs)
        self.tax_rate = tax_rate

    @property
    def payment_table(self):
        return self.wrapped_mortgage.payment_table

    @property
    def monthly_installment(self):
        return self.wrapped_mortgage.monthly_installment

    @property
    def principle(self):
        return self.wrapped_mortgage.principle

    @property
    def initial_equity_cost(self):
        return self.wrapped_mortgage.initial_equity_cost

    def total_interest(self, years):
        return self.wrapped_mortgage.total_interest(years) * (1 - self.tax_rate)

class EarlyRepaymentMortgage(Mortgage):
    def __init__(self, tax_rate, MortgageClassToDecorate, *mortgage_class_args, **mortgage_class_kwargs):
        super().__init__()
        self.wrapped_mortgage = MortgageClassToDecorate(*mortgage_class_args, **mortgage_class_kwargs)
        self.tax_rate = tax_rate

    @property
    def payment_table(self):
        return self.wrapped_mortgage.payment_table

    @property
    def monthly_installment(self):
        return self.wrapped_mortgage.monthly_installment

    @property
    def principle(self):
        return self.wrapped_mortgage.principle

    @property
    def initial_equity_cost(self):
        return self.wrapped_mortgage.initial_equity_cost

    def total_interest(self, years):
        return self.wrapped_mortgage.total_interest(years)


# print(TaxDeductibleMortgage(372000, 25, interest_rate, 0.2).payment_table)
# print(TaxDeductibleMortgage(372000, 25, interest_rate, 0.2).total_interest)

# Property value = net cash inflows each year (after interest only mortgage/repayment mortgage + fees, taking into account tax reductions), over x years +projected vlaue - fees and taxes of buying and sale - original price.)

class Investment:
    # def initial_equity_cost():
    # def gross_buy_price():
    # def sell_cost():
    # def calculate_profits():
    # def initial_equity():
    # Handle capital appreciation here.
    def nominal_return_on_investment(self, years, annual_price_change_percentage, annual_inflation_percentage):
        buy_fees = self.buy_expenses
        sell_price = self.buy_price * (1 + annual_price_change_percentage) ** years
        # print(f"buy price: {self.buy_price} sell_price: {sell_price} years: {years}")
        sell_fees = self.sell_expenses(sell_price, years)
        profits = self.calculate_profits(years)

        initial_purchase_cost = self.initial_equity_cost
        return sell_price - sell_fees - buy_fees + profits - initial_purchase_cost

    def percentage_return_on_investment(self, years, annual_price_change_percentage, annual_inflation_percentage):
        initial_purchase_cost = self.initial_equity_cost
        future_return = self.nominal_return_on_investment(years, annual_price_change_percentage,
                                                          annual_inflation_percentage)
        # return ((future_return + initial_purchase_cost) / initial_purchase_cost) - 1
        return future_return / initial_purchase_cost

    def annual_percentage_return_on_investment(self, years, annual_price_change_percentage,
                                               annual_inflation_percentage):
        total_percentage = self.percentage_return_on_investment(years, annual_price_change_percentage,
                                                                annual_inflation_percentage)
        # TODO deal with negative total percentages in a more robust way
        if total_percentage < 0:
            total_percentage *= -1
            result = (total_percentage + 1) ** (1 / years) - 1
            result *= -1
            return result
        return (total_percentage + 1) ** (1 / years) - 1


def calculateCapitalGains(is_property, price_gain):
    capital_gains_allowance = 12300
    if (price_gain <= capital_gains_allowance):
        return 0
    else:
        if is_property:
            capital_gains_tax_rate = 0.28
        else:
            capital_gains_tax_rate = 0.20
        return (price_gain - capital_gains_allowance) * capital_gains_tax_rate


class Property(Investment):
    def __init__(self, second_property, property_value, mortgage, monthly_gross_rental, rental_tax,
                 months_occupied_out_of_12, agency_percentage):
        SOLICITOR_FEES = 3776
        self._buy_fees = calculateSDLT(second_property, property_value) + SOLICITOR_FEES
        self.property_value = property_value
        self.monthly_gross_rental = monthly_gross_rental
        self.months_occupied_out_of_12 = months_occupied_out_of_12
        self.agency_percentage = agency_percentage
        self.rental_tax = rental_tax
        self.mortgage = mortgage

    @property
    def buy_expenses(self):
        return self._buy_fees

    @property
    def buy_price(self):
        return self.property_value

    def calculate_profits(self, years):
        return self.monthly_gross_rental * self.months_occupied_out_of_12 * years * (
                1 - self.agency_percentage - self.rental_tax) - self.mortgage.total_fees(years)

    @property
    def initial_equity_cost(self):
        return self.property_value - self.mortgage.principle

    def sell_expenses(self, sell_price, years):
        if len(self.mortgage.payment_table.index) > years * 12:
            mortgage_row = self.mortgage.payment_table.loc[years * 12 - 1]
            mortgage_to_payoff = mortgage_row["Principle"] + mortgage_row["Interest"] - mortgage_row["Payment"]
        else:
            mortgage_to_payoff = 0
        solicitor_fees = 4000
        capital_gains_tax = calculateCapitalGains(True, sell_price - self.buy_price)
        return capital_gains_tax + solicitor_fees + mortgage_to_payoff


class LeaseholdProperty(Property):
    def __init__(self, second_property, property_value, mortgage, monthly_gross_rental, rental_tax,
                 months_occupied_out_of_12, agency_percentage, annual_service_charge, annual_ground_rent,
                 will_you_live_in_this=True):
        super().__init__(second_property, property_value, mortgage, monthly_gross_rental, rental_tax,
                         months_occupied_out_of_12, agency_percentage)
        self.annual_service_charge = annual_service_charge
        self.annual_ground_rent = annual_ground_rent
        self.will_you_live_in_this = will_you_live_in_this

    def calculate_profits(self, years):
        if self.will_you_live_in_this:
            return super().calculate_profits(years) - (self.annual_service_charge + self.annual_ground_rent)
        else:
            return super().calculate_profits(years) - (self.annual_service_charge + self.annual_ground_rent) * (
                        1 - self.rental_tax)


class HLStock(Investment):
    def __init__(self, stock_value, price_to_earnings, yearly_topups=[]):
        self.ESTIMATED_FX_SPREAD = 0.00259669736
        self.ESTIMATED_FX_CHARGE = 0.00998212157
        self.ESTIMATED_BUY_COMMISSION = 11.95
        self.ESTIMATED_SELL_COMMISSION = 11.95
        self._buy_fees = (
                                 self.ESTIMATED_FX_SPREAD + self.ESTIMATED_FX_CHARGE) * stock_value + self.ESTIMATED_BUY_COMMISSION
        self.stock_value = stock_value
        self.price_to_earnings = price_to_earnings
        self.yearly_topups = yearly_topups

    @property
    def buy_expenses(self):
        return self._buy_fees

    @property
    def buy_price(self):
        return self.stock_value

    def calculate_profits(self, years):
        future_value = self.buy_price
        for year in range(1, years + 1):
            #print(year-1)
            future_value = future_value * (1 + (1.0 / self.price_to_earnings))
            if len(self.yearly_topups) >= year:
                #print(future_value)
                #print(self.yearly_topups[year-1])
                future_value += self.yearly_topups[year-1]
                #print(future_value)
                #print()
        future_value -= self.buy_price
        return future_value

    @property
    def initial_equity_cost(self):
        return self.stock_value

    def sell_expenses(self, sell_price, years):
        # TODO consider CGT, it seems negligible because the gain is so avoidable...
        return (self.ESTIMATED_FX_CHARGE) * self.stock_value + self.ESTIMATED_SELL_COMMISSION


def _mortgageFactory(mortgageClass, monthly_gross_rental_floor, smallest_principle, largest_principle, **kwargs):
    # HSBC, Mojo, Skipton
    # BENCHMARK_INTEREST_RATE = 0.055
    # Metro
    BENCHMARK_INTEREST_RATE = 0.05
    original_interest_rate = kwargs["interest_rate"]
    kwargs["interest_rate"] = BENCHMARK_INTEREST_RATE
    while smallest_principle < largest_principle:
        # print(f"smallest_principle {smallest_principle}, largest_principle {largest_principle}")
        principle_to_check = (largest_principle + smallest_principle) / 2
        kwargs["principle"] = principle_to_check
        mortgage_to_check = mortgageClass(**kwargs)
        monthly_installment = mortgage_to_check.monthly_installment
        # print(f"monthly_gross_rental_floor {monthly_gross_rental_floor}, monthly_installment {monthly_installment}")
        if monthly_gross_rental_floor < monthly_installment:
            largest_principle = principle_to_check - 1
        elif monthly_gross_rental_floor > monthly_installment:
            smallest_principle = principle_to_check + 1
    kwargs["interest_rate"] = original_interest_rate
    max_mortgage_that_passes_checks = mortgageClass(**kwargs)
    return max_mortgage_that_passes_checks


def BTLmortgageFactory(MortgageClass, monthly_gross_rental, property_price, ltv_percentage, **kwargs):
    # HSBC, Mojo, Skipton
    # monthly_gross_rental_floor = monthly_gross_rental / 1.45
    # Metro
    monthly_gross_rental_floor = monthly_gross_rental / 1.4

    return _mortgageFactory(MortgageClass, monthly_gross_rental_floor, 0, property_price * ltv_percentage,
                            **kwargs)


def mortgageFactory(MortgageClass, monthly_gross_rental, property_price, ltv_percentage, **kwargs):
    # For residential mortgages rental income is not a factor, make it crazy high so that the check is never failed.
    monthly_gross_rental_floor = 999999

    return _mortgageFactory(MortgageClass, monthly_gross_rental_floor, 0, property_price * ltv_percentage,
                            **kwargs)


interest_rate = 0.017


# print(InterestOnlyMortgage(75000, 25, interest_rate).payment_table)
# TODO If I go for the most leverage calculate_profits will be near or below 0, because of rental tax > tax_rate and mortgageFactory currently uses a more optimistic measurement of rental income than calculate_profits. perhaps they should use the same measurement?
# Share composite class with Property called RentalIncome? Or use the profit method in property without a mortgage directly to derive a 0?

def generatePropertyForecast(is_second_property, principle, ltv_percentage, monthly_gross_rental, rental_tax,
                             months_occupied_out_of_12,
                             agency_percentage, MortgageClass, **mortgage_kwargs):
    mortgage = mortgageFactory(MortgageClass, monthly_gross_rental, principle, ltv_percentage, **mortgage_kwargs)
    property_forecast = Property(is_second_property, principle, mortgage,
                                 monthly_gross_rental=monthly_gross_rental, rental_tax=rental_tax,
                                 months_occupied_out_of_12=months_occupied_out_of_12,
                                 agency_percentage=agency_percentage)
    return property_forecast


def generateLeaseholdPropertyForecast(is_second_property, principle, ltv_percentage, monthly_gross_rental, rental_tax,
                                      months_occupied_out_of_12,
                                      agency_percentage, annual_service_charge, annual_ground_rent, mortgage_searcher,
                                      MortgageClass, **mortgage_kwargs):
    mortgage = mortgage_searcher(MortgageClass, monthly_gross_rental, principle, ltv_percentage=ltv_percentage,
                                 **mortgage_kwargs)
    property_forecast = LeaseholdProperty(is_second_property, principle, mortgage,
                                          monthly_gross_rental=monthly_gross_rental, rental_tax=rental_tax,
                                          months_occupied_out_of_12=months_occupied_out_of_12,
                                          agency_percentage=agency_percentage,
                                          annual_service_charge=annual_service_charge,
                                          annual_ground_rent=annual_ground_rent)
    return property_forecast


def generateLiveInLandlordPropertyForecast(is_second_property, principle, ltv_percentage, monthly_gross_rental,
                                           rental_tax, months_occupied_out_of_12,
                                           agency_percentage, MortgageClass, **mortgage_kwargs):
    mortgage = MortgageClass(principle=principle * ltv_percentage, **mortgage_kwargs)
    property_forecast = Property(is_second_property, principle, mortgage,
                                 monthly_gross_rental=monthly_gross_rental, rental_tax=rental_tax,
                                 months_occupied_out_of_12=months_occupied_out_of_12,
                                 agency_percentage=agency_percentage)
    return property_forecast


# TODO am I calculating capital gains correctly
# TODO mortgatefactory shoudl have an ltv limit.
# TODO taxpayer model

if __name__ == "__main__":
    ltv_percentage = 0.75
    interest_rate = 0.0259
    # interest_rate = 0.05
    # interest_rate = 0.0146
    asset_dictionary = {}

    # asset_dictionary["BRK.B 21 P/E"] = HLStock(250000, 21.73)

    #     asset_dictionary["BRK.B 15 P/E"] = HLStock(150000, 15)

    #     asset_dictionary["BRK.B 10 P/E"] = HLStock(150000, 10)

    #     # asset_dictionary["BRK.B 7 P/E"] = HLStock(200000, 7)

    #     property_forecast = generatePropertyForecast(True, 100000, ltv_percentage=ltv_percentage, monthly_gross_rental=750, rental_tax=0.45,
    #                                                  months_occupied_out_of_12=10,
    #                                                  agency_percentage=.2, MortgageClass=TaxDeductibleMortgage,
    #                                                  MortgageClassToDecorate=RepaymentMortgage, tax_rate=0.2, length=25,
    #                                                  interest_rate=0.03)
    #     #asset_dictionary["High Yield Property"] = property_forecast

    #     property_forecast = generatePropertyForecast(True, 220000, ltv_percentage=ltv_percentage, monthly_gross_rental=800, rental_tax=0.45,
    #                                                  months_occupied_out_of_12=10,
    #                                                  agency_percentage=.2, MortgageClass=TaxDeductibleMortgage,
    #                                                  MortgageClassToDecorate=RepaymentMortgage, tax_rate=0.2, length=25,
    #                                                  interest_rate=0.03)
    #     #asset_dictionary["Albany Gardens, Hythe"] = property_forecast

    #     property_forecast = generatePropertyForecast(True, 220000, ltv_percentage=ltv_percentage, monthly_gross_rental=800, rental_tax=0.2,
    #                                                  months_occupied_out_of_12=10,
    #                                                  agency_percentage=.2, MortgageClass=TaxDeductibleMortgage,
    #                                                  MortgageClassToDecorate=RepaymentMortgage, tax_rate=0.2, length=25,
    #                                                  interest_rate=0.03)
    #     #asset_dictionary["Albany Gardens, Hythe, Non Resident"] = property_forecast

    #     property_forecast = generatePropertyForecast(True, 100000, ltv_percentage=ltv_percentage, monthly_gross_rental=750, rental_tax=0.45,
    #                                                  months_occupied_out_of_12=10,
    #                                                  agency_percentage=.2, MortgageClass=TaxDeductibleMortgage,
    #                                                  MortgageClassToDecorate=RepaymentMortgage, tax_rate=0.2, length=25,
    #                                                  interest_rate=0.10)
    #     asset_dictionary["10% Interest World Property"] = property_forecast

    property_forecast = generateLeaseholdPropertyForecast(True, 750000, ltv_percentage=ltv_percentage,
                                                          monthly_gross_rental=(700 + 700 * 3), rental_tax=0.45,
                                                          months_occupied_out_of_12=10,
                                                          agency_percentage=.2, annual_service_charge=1500,
                                                          annual_ground_rent=90, mortgage_searcher=mortgageFactory,
                                                          MortgageClass=TaxDeductibleMortgage,
                                                          MortgageClassToDecorate=RepaymentMortgage, tax_rate=0.2,
                                                          length=25,
                                                          interest_rate=0.0259)

    asset_dictionary["Cookham House"] = property_forecast

    #     property_forecast = generateLiveInLandlordPropertyForecast(False, 525000, 0.8, monthly_gross_rental=(500 + 100 * 2),
    #                                                                rental_tax=0.45,
    #                                                                months_occupied_out_of_12=10,
    #                                                                agency_percentage=.2,
    #                                                                MortgageClass=TaxDeductibleMortgage,
    #                                                                MortgageClassToDecorate=RepaymentMortgage, tax_rate=0.2,
    #                                                                length=25,
    #                                                                interest_rate=0.0259)
    #     #asset_dictionary["Grandby House"] = property_forecast

    lixing_agency_percentage = (0.075 + 0.025) * 1.20
    asset_dictionary["2 Bed 1 bath long and waterson"] = generateLeaseholdPropertyForecast(True, 690000,
                                                                                           ltv_percentage=ltv_percentage,
                                                                                           # monthly_gross_rental=700 * 4.3,
                                                                                           monthly_gross_rental=625,
                                                                                           rental_tax=0,
                                                                                           months_occupied_out_of_12=12,
                                                                                           agency_percentage=lixing_agency_percentage,
                                                                                           annual_service_charge=7 * 677,
                                                                                           annual_ground_rent=600,
                                                                                           mortgage_searcher=mortgageFactory,
                                                                                           MortgageClass=RepaymentMortgage,
                                                                                           length=25,
                                                                                           interest_rate=interest_rate)

    #     asset_dictionary["3 Bed 2 bath long and waterson"] = generateLeaseholdPropertyForecast(True, 1180000, ltv_percentage=ltv_percentage, monthly_gross_rental=1100*4.3, rental_tax=0.45,
    #                                                  months_occupied_out_of_12=10,
    #                                                  agency_percentage=.2, annual_service_charge=7*1264, annual_ground_rent=600, MortgageClass=TaxDeductibleMortgage,
    #                                                  MortgageClassToDecorate=RepaymentMortgage, tax_rate=0.2, length=25,
    #                                                  interest_rate=0.0259)

    atlas_price = 980000
    # atlas_price = 900000

    # Recently sold for this price.
    heron_property_price = 535000
    heron_property_price = 600000
    asset_dictionary["Heron - Studio"] = generateLeaseholdPropertyForecast(True, heron_property_price,
                                                                           ltv_percentage=ltv_percentage,
                                                                           # monthly_gross_rental=3467,
                                                                           monthly_gross_rental=0,
                                                                           rental_tax=0,
                                                                           months_occupied_out_of_12=10,
                                                                           agency_percentage=0,
                                                                           annual_service_charge=3967,
                                                                           annual_ground_rent=300,
                                                                           mortgage_searcher=mortgageFactory,
                                                                           MortgageClass=RepaymentMortgage,
                                                                           length=25,
                                                                           interest_rate=interest_rate)


    # asset_dictionary["BRK.B 40 P/E"] = HLStock(250000, 40, yearly_principle_repayment-2535*12)
    # asset_dictionary["BRK.B 40 P/E"] = HLStock(535000*.25, 40, yearly_principle_repayment-2535*12)

    def generateHeaderTableAndGraphSource():

        headers = ["Asset Name", "Initial Equity Cost", "Nominal ROI", "% ROI", "% ROI Year on Year", "Nominal Profit"]
        table = []

        years_to_forecast = 50
        graph_source = pd.DataFrame(index=np.arange(0, years_to_forecast * len(asset_dictionary)),
                                    columns=["Asset Name", "Year", "Nominal ROI", "% ROI Year on Year", "% ROI",
                                             "Nominal Profit"])
        inflation_rate = 0.01
        j = 0
        for key, value in asset_dictionary.items():

            for i in range(0, years_to_forecast):
                years = i + 1
                # graph_source.loc[i] = [[key, value.initial_equity_cost + value.nominal_return_on_investment(years, 0, 0), value.percentage_return_on_investment(years, 0, 0), value.annual_percentage_return_on_investment(years, 0, 0)]]
                if years == 1:
                    roi_this_year = value.percentage_return_on_investment(years, inflation_rate, 0)
                    profit_this_year = value.calculate_profits(years)
                else:
                    roi_this_year = value.percentage_return_on_investment(years, inflation_rate,
                                                                          0) - value.percentage_return_on_investment(
                        years - 1, inflation_rate, 0)
                    profit_this_year = value.calculate_profits(years) - value.calculate_profits(years - 1)
                graph_source.loc[j + i] = [key, years,
                                           value.nominal_return_on_investment(years, inflation_rate, 0),
                                           value.annual_percentage_return_on_investment(years, inflation_rate, 0),
                                           roi_this_year, profit_this_year]
                row = [key, value.initial_equity_cost, value.nominal_return_on_investment(25, 0, 0),
                       value.percentage_return_on_investment(25, 0.01, 0),
                       value.annual_percentage_return_on_investment(25, inflation_rate, 0), profit_this_year]
            table.append(row)
            # print(f"{key} {years} {value.initial_equity_cost + value.nominal_return_on_investment(years, 0, 0)}")
            j += years_to_forecast
        return headers, table, graph_source


    (headers, table, graph_source) = generateHeaderTableAndGraphSource()
    print(tabulate(table, headers, tablefmt="presto"))
    alt.renderers.enable('html')

stock_price_to_earnings = 35
# stock_price_to_earnings = 80
cost_of_renting_alone = 2535
cost_of_renting_alone = 2250
cost_of_renting_alone = 1842
cost_of_renting_alone = 2000
cost_of_renting_alone = 2250
atlas_fully_rented_out = 3467
atlas_fully_rented_out = 3067
atlas_studio_property_price = 550000

# TODO model typical stocks, BRK.A / Index funds?
# TODO would be nice to know what what interest rate a given property becomes not worth it.
# Double check profit and loss maths are correct
# alt.Chart(graph_source).mark_line().encode(x='Year', y='Nominal ROI', color='Asset Name', strokeDash='Asset Name').properties(width=700, height=700)
# alt.Chart(graph_source[graph_source["Asset Name"] == "10% Interest World Property"]).mark_line().encode(x='Year', y='Nominal ROI', color='Asset Name', strokeDash='Asset Name')