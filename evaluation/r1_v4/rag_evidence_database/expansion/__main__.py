"""Resumable expansion builder CLI; source retrieval remains the existing database API."""
import argparse,resource
from evaluation.r1_v4.provenance import canonical
from .build import populate

def main():
 resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3))
 p=argparse.ArgumentParser();p.add_argument('database');args=p.parse_args()
 print(canonical(populate(args.database)).decode())
if __name__=='__main__':main()
