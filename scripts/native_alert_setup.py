"""Prepare date-watch links. Does not create alerts or access any account."""
import argparse
import csv
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import tracker


def write_links(path):
    with path.open('w',newline='') as output:
        writer=csv.writer(output)
        writer.writerow(['departure','return','days_between_departures','google_flights_search_link',
                         'native_watch_enabled_by_user','account_watch_capacity_verified'])
        for depart,back in tracker.date_pairs():
            writer.writerow([depart.isoformat(),back.isoformat(),(back-depart).days,
                tracker.flight_link(depart.isoformat(),back.isoformat()),False,False])


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();write_links(args.output)
    print(f'Prepared {len(tracker.date_pairs())} links. No watches have been created.')
