import numpy as np
import pandas as pd
from utils.gcsp.helpers import load_questions

RV = 1/1.04

def calculate_sri_responses(question_data, min_sri, max_sri):
    questions = load_questions()
    df = pd.DataFrame(questions)

    weights = df.set_index("key")["weights"].to_dict()

    total_weighted = 0
    total_weight = 0

    for key, value in question_data.items():
        if key in weights:
            total_weighted += int(value) * weights[key]
            total_weight += weights[key]

    if total_weight == 0:
        weighted_score = 3  # default middle
    else:
        weighted_score = total_weighted / total_weight

    score = (5 - weighted_score) / 4 * (max_sri - min_sri) + min_sri
    return {
        "weighted_score": round(weighted_score, 1),
        "score": round(score, 0)
    }

def main_calc(form_data):
    """
    Main entry point for calculations.
    - Extracts question responses and other form inputs
    - Calls calculate_sri_responses for weighted score and SRI
    """

    # Extract the SRI-related inputs
    min_sri = int(form_data.get("minsri", 0))
    max_sri = int(form_data.get("maxsri", 100))

    question_data = {
        k: v for k, v in form_data.items()
        if k not in ["age", "gender", "retirementFund", "minsri", "maxsri"]
    }

    sri_results = calculate_sri_responses(question_data, min_sri, max_sri)
    sri_score = round(sri_results["score"], 0)

    # Explicit fields
    age = int(form_data.get("age"))
    gender = form_data.get("gender")
    retirementFund = form_data.get("retirementFund")
    retirement_fund = int(retirementFund.replace(",", ""))
    result = do_gcsp(age, gender, retirement_fund, sri_score/100, 4, 0)

    return {
        "score": sri_score,
        "weighted_score": sri_results["weighted_score"],
        "age": age,
        "gender": gender,
        "retirementFund": retirementFund,
        "minsri": min_sri,
        "maxsri": max_sri,
        "GCSP_result": result
    }


# ideally using API. Below is the core calculation of GCSP API
def do_gcsp(age, gender, total_fund, spia_pct, asset_low_index, asset_high_index):
    asset_classes = pd.read_csv("utils/gcsp/data/asset_classes.csv")
    rand_low = pd.read_csv("utils/gcsp/data/rand_low.csv", header=None)
    rand_high = pd.read_csv("utils/gcsp/data/rand_high.csv", header=None)
    low_mean = asset_classes.loc[asset_low_index, '20Year']
    low_vol = asset_classes.loc[asset_low_index, 'stddev']
    high_mean = asset_classes.loc[asset_high_index, '20Year']
    high_vol = asset_classes.loc[asset_high_index, 'stddev']

    low_return = np.exp(low_mean - 0.5 * pow(low_vol, 2) + low_vol * rand_low)
    high_return = np.exp(high_mean - 0.5 * pow(high_vol, 2) + high_vol * rand_high)
    nYears = 95 - age
    optimal = get_pureOptimal(nYears, low_return, high_return)
    bm_low = round(optimal['low_asset_weight'], 2)
    bm_spending = round(optimal['spending95'] * total_fund)
    life_parameter = get_annuity(age, gender)
    bm_gcsp = get_gcsp(121-age, bm_low, low_return, high_return, total_fund, bm_spending, 0, life_parameter)
    mix_strategy = match_gcsp(121-age, bm_gcsp, bm_low, low_return, high_return, total_fund, spia_pct, life_parameter)
    mix_low = round(mix_strategy['mix_low'], 2)
    mix_gcsp = mix_strategy['mix_gcsp']
    #mix_spending = round(get_spending_by_ruin(nYears, mix_low, low_return, high_return, 0.05) * total_fund * (1-spia_pct))
    annuity_pay = round(total_fund * spia_pct * life_parameter['spia_payoutRatio'])
    mix_withdraw_arr = get_withdraw_percentile(nYears, mix_low, low_return, high_return) * total_fund * (1-spia_pct) + annuity_pay
    mix_spending = round(mix_withdraw_arr[49])

    bm_withdraw_arr = get_withdraw_percentile(nYears, bm_low, low_return, high_return) * total_fund
    # The indices for the 1th, 5th, 10th, 20th, 30th, ..., 90th, 95th percentile 
    indices = [9, 49, 99, 199, 299, 399, 499, 599, 699, 799, 899, 949]
    mix_spending_arr = [round(mix_withdraw_arr[i]) for i in indices]
    bm_spending_arr = [round(bm_withdraw_arr[i]) for i in indices]

    return {'bm_asset': total_fund,
            'bm_spending': round(bm_spending), 
            'bm_gcsp': bm_gcsp, 
            'bm_low_high': [bm_low,1-bm_low], 
            'bm_low_high_amt': [bm_low * total_fund,(1-bm_low) * total_fund],
            'mix_asset': total_fund*(1-spia_pct),
            'mix_spiaAmt': total_fund * spia_pct,
            'mix_low_high': [mix_low,1-mix_low], 
            'mix_low_high_amt': [
    mix_low * total_fund * (1 - spia_pct),
    (1 - mix_low) * total_fund * (1 - spia_pct)
],
            'mix_spending': round(mix_spending), 
            'mix_gcsp': mix_gcsp,
            'mix_spia_pay': round(annuity_pay), 
            'mix_spending_arr': mix_spending_arr,
            'bm_spending_arr': bm_spending_arr
            }


def get_annuity(age, gender):
    mort_tbl = pd.read_csv("utils/gcsp/data/mortality.csv")
    qx_array = mort_tbl[gender].to_numpy()
    qx = qx_array[age-50:]
    px = 1-qx
    tpx = np.cumprod(px)
    v = RV ** np.arange(1, len(tpx)+1)
    spia_premium = sum(tpx * v) + 1
    spia_payoutRatio = 1/spia_premium
    tslashqx = qx * (np.concatenate((1, tpx[:-1]), axis=None))

    return {'spia_premium': spia_premium, 'spia_payoutRatio': spia_payoutRatio, 'tslashqx': tslashqx}


def get_spending_by_ruin(nYears, lw, low_return, high_return, failure_rate):
    hw = 1-lw
    port_return = low_return * lw + high_return * hw
    port_return = port_return.iloc[:nYears]
    port_return = port_return.to_numpy()
    port_v = 1 / port_return
    port_cum_v = np.cumprod(port_v, axis=0)
    spending_pv = np.sum(port_cum_v, axis=0)
    spending_factor = 1/(1+spending_pv)
    spending_factor = np.sort(spending_factor)

    return spending_factor[round(1000 * failure_rate -1)]


def get_pureOptimal(nYears, low_return, high_return):
    optimal_lw = 0
    optimal_spending = 0

    for lw in range(1, 99):
        spending_95 = get_spending_by_ruin(nYears, lw/100, low_return, high_return, 0.05)
        if spending_95 > optimal_spending:
            optimal_lw = lw/100
            optimal_spending = spending_95

    return {'low_asset_weight': optimal_lw, 'spending95': optimal_spending}


def get_gcsp(nYears, lw, low_return, high_return, total_fund, spending, spia_pct, life_parameter):
    hw = 1 - lw
    port_return = low_return * lw + high_return * hw
    port_return = port_return.to_numpy()
    tslashqx = life_parameter['tslashqx']
    discount_factor = pow(1/1.04, np.arange(1, nYears+1))
    annuity_discount_factor = tslashqx * discount_factor
    spia_pay = total_fund * spia_pct * life_parameter['spia_payoutRatio']
    withdraw = spending - spia_pay
    acct_matrix = np.zeros((nYears, 1000))
    acct_matrix[0] = (total_fund * (1-spia_pct) - withdraw) * port_return[0]
    for i in range(1, nYears):
        acct_matrix[i] = (acct_matrix[i-1] - withdraw) * port_return[i]

    acct_apv = np.dot(annuity_discount_factor, acct_matrix)
    income_apv = sum(np.cumsum((withdraw + spia_pay) * discount_factor * 1.04) * tslashqx)
    total_apv = acct_apv + income_apv
    gcsp = np.mean(total_apv)/np.std(total_apv)
    return round(gcsp, 3)


def match_gcsp(nYears, bm_gcsp, bm_low, low_return, high_return, total_fund, spia_pct, life_parameter):
    step_width = 0.01
    low_weight = bm_low
    counter = 1
    mix_gcsp = bm_gcsp # set mix_gcsp default value
    while low_weight >0 and counter < 100:
        low_weight = low_weight - step_width
        spending_ratio = get_spending_by_ruin(nYears=nYears-25, lw=low_weight, low_return=low_return, high_return=high_return, failure_rate=0.05)
        spending = spending_ratio  * total_fund * (1-spia_pct) + total_fund * spia_pct * life_parameter['spia_payoutRatio']
        mix_gcsp = get_gcsp(nYears, low_weight, low_return, high_return, total_fund, spending, spia_pct, life_parameter)
        if abs(mix_gcsp - bm_gcsp) < 0.01:
            break
        if mix_gcsp < bm_gcsp:
            low_weight = low_weight + step_width
            step_width = step_width/4
        counter = counter + 1

    return {'mix_low': low_weight, 'mix_gcsp': mix_gcsp}

def get_withdraw_percentile(nYears, lw, low_return, high_return):
    hw = 1-lw
    port_return = low_return * lw + high_return * hw
    port_return = port_return.iloc[:nYears]
    port_return = port_return.to_numpy()
    port_v = 1 / port_return
    port_cum_v = np.cumprod(port_v, axis=0)
    spending_pv = np.sum(port_cum_v, axis=0)
    spending_factor = 1/(1+spending_pv)
    spending_factor = np.sort(spending_factor)

    return spending_factor
