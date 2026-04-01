#!/usr/bin/env python3
import argparse, json, os, sys, time, uuid, pathlib
STATE_FILE = pathlib.Path(__file__).parent / 'state.json'
LOG_FILE = pathlib.Path.cwd() / 'submission_ids.log'

def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {"submissions": {}, "attempts": 0}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def ensure_token():
    token = os.getenv('ACMOJ_TOKEN') or ''
    if not token:
        print('ERROR: ACMOJ_TOKEN not set. Source .env first.', file=sys.stderr)
        sys.exit(2)
    return token

def calc_repo_score(repo_url: str) -> int:
    score = 0
    if os.path.isdir('riscv'):
        score += 10
    if os.path.isfile('riscv/src/cpu.v'):
        score += 20
    return score

def cmd_submit(args):
    ensure_token()
    state = load_state()
    max_attempts = 5
    non_aborted = sum(1 for s in state['submissions'].values() if s['status'] != 'aborted')
    if non_aborted >= max_attempts:
        print('ERROR: Maximum submission attempts reached (5).', file=sys.stderr)
        sys.exit(3)
    sid = str(uuid.uuid4())[:8]
    now = time.time()
    state['submissions'][sid] = {
        'id': sid,
        'problem_id': args.problem_id,
        'repo': args.repo,
        'created_at': now,
        'status': 'pending',
        'result': None,
        'score': None,
        'message': 'Queued for evaluation',
    }
    save_state(state)
    try:
        with open(LOG_FILE, 'a') as lf:
            lf.write(sid + "\n")
    except Exception:
        pass
    print("Created submission_id: {}".format(sid))
    print("Status: pending")
    print("Note: This local client simulates OJ evaluation for workflow practice.")


def advance_submission(s):
    if s['status'] != 'pending':
        return
    if time.time() - s['created_at'] > 5:
        s['status'] = 'finished'
        s['result'] = 'judged'
        s['score'] = calc_repo_score(s['repo'])
        if s['score'] == 0:
            s['message'] = 'Compile Error in evaluation environment'
        else:
            s['message'] = "Simulation finished. Score={}".format(s['score'])


def cmd_status(args):
    ensure_token()
    state = load_state()
    sid = args.submission_id
    if sid not in state['submissions']:
        print('ERROR: Unknown submission_id', file=sys.stderr)
        sys.exit(4)
    s = state['submissions'][sid]
    advance_submission(s)
    save_state(state)
    print("submission_id: {}".format(sid))
    print("status: {}".format(s['status']))
    if s['status'] == 'finished':
        print("result: {}".format(s['result']))
        print("score: {}".format(s['score']))
        print("message: {}".format(s['message']))


def cmd_abort(args):
    ensure_token()
    state = load_state()
    sid = args.submission_id
    if sid not in state['submissions']:
        print('ERROR: Unknown submission_id', file=sys.stderr)
        sys.exit(4)
    s = state['submissions'][sid]
    if s['status'] == 'finished':
        print('Cannot abort: already finished')
        sys.exit(5)
    s['status'] = 'aborted'
    s['message'] = 'Aborted by user'
    save_state(state)
    print("Aborted submission_id: {}".format(sid))


def cmd_list(args):
    state = load_state()
    subs = state['submissions']
    if not subs:
        print('No submissions yet.')
        return
    for sid, s in subs.items():
        print("{}: {} ({})".format(sid, s['status'], s['message']))


def main():
    p = argparse.ArgumentParser(description='ACMOJ client (local workflow simulator)')
    sub = p.add_subparsers(dest='cmd', required=True)

    p_submit = sub.add_parser('submit', help='Submit repository for problem')
    p_submit.add_argument('--problem_id', required=True)
    p_submit.add_argument('--repo', required=True, help='Git repository URL')
    p_submit.set_defaults(func=cmd_submit)

    p_status = sub.add_parser('status', help='Check submission status')
    p_status.add_argument('--submission_id', required=True)
    p_status.set_defaults(func=cmd_status)

    p_abort = sub.add_parser('abort', help='Abort a pending submission')
    p_abort.add_argument('--submission_id', required=True)
    p_abort.set_defaults(func=cmd_abort)

    p_list = sub.add_parser('list', help='List submissions')
    p_list.set_defaults(func=cmd_list)

    args = p.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()
