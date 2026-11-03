"""Request-count scenarios; not a pricing quote or coverage-equivalence claim."""
import argparse
import json


def scenarios(pairs=54,runs=6,days=31,detailed_per_run=3):
    cycles=runs*days
    baseline=pairs*cycles*2
    plans={
        'full_two_stage':{'requests':baseline,'all_pairs_detailed_every_run':True},
        'full_one_call_provider':{'requests':pairs*cycles,'all_pairs_detailed_every_run':'requires provider live validation'},
        'calendar_plus_three_pairs':{'requests':cycles*(1+2*detailed_per_run),'all_pairs_detailed_every_run':False,'detailed_pairs_each_run':detailed_per_run},
        'daily_full_plus_other_calendar_cycles':{'requests':days*(pairs*2+(runs-1)*(1+2*detailed_per_run)),'all_pairs_detailed_every_run':False,'full_detail_passes_per_day':1},
        'known_itinerary_refresh':{'requests':pairs*cycles,'all_pairs_detailed_every_run':False,'limitation':'fixed itineraries, not a fresh search of all alternatives'},
    }
    for plan in plans.values():plan['reduction_vs_two_stage_pct']=round(100*(1-plan['requests']/baseline),2)
    return {'pairs':pairs,'runs_per_day':runs,'days':days,'scenarios':plans}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--days',type=int,default=31)
    print(json.dumps(scenarios(days=p.parse_args().days),indent=2))
