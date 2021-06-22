import json
import os
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("--project", required=True)

    parser.add_argument("--filter", required=True)

    parser.add_argument("--weeks",
                        required=True, type=int)

    parser.add_argument("--days",
                        required=True, type=int)

    parser.add_argument("--hours",
                        required=True, type=int)

    parser.add_argument("--output_file_name", required=True)

    args = parser.parse_args()

    msg = {"project_id": args.project,
           "filter": args.filter,
           "weeks": args.weeks,
           "days": args.days,
           "hours": args.hours,
           "output_file_name": args.output_file_name}

    if not os.path.exists("msg_tmp/"):
        os.makedirs("msg_tmp/")

    with open('../../msg_tmp/msg.json', 'w') as fp:
        json.dump(msg, fp)
