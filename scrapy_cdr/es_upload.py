import argparse
from datetime import datetime
from itertools import islice
import time

import json_lines
import elasticsearch
import elasticsearch.helpers

from .utils import format_timestamp


def main():
    parser = argparse.ArgumentParser(description='Upload items to ES index')
    arg = parser.add_argument
    arg('input', help='input in .jl or .jl.gz format')
    arg('index', help='ES index name')
    arg('--type', default='document',
        help='ES type to use ("document" by default)')
    arg('--op-type', default='index',
        choices={'index', 'create', 'delete', 'update'},
        help='ES operation type to use ("document" by default)')
    arg('--broken', action='store_true',
        help='specify if input might be broken (incomplete)')
    arg('--host', default='localhost', help='ES host in host[:port] format')
    arg('--user', help='HTTP Basic Auth user')
    arg('--password', help='HTTP Basic Auth password')
    arg('--chunk-size', type=int, default=50, help='upload chunk size')
    arg('--threads', type=int, default=8, help='number of threads')
    arg('--limit', type=int, help='Index first N items')

    args = parser.parse_args()
    kwargs = {}
    if args.user or args.password:
        kwargs['http_auth'] = (args.user, args.password)

    client = elasticsearch.Elasticsearch(
        [args.host],
        connection_class=elasticsearch.RequestsHttpConnection,
        timeout=600,
        **kwargs)
    print(client.info())

    def actions():
        with json_lines.open(args.input, broken=args.broken) as f:
            items = islice(f, args.limit) if args.limit else f
            for item in items:
                item['timestamp_index'] = format_timestamp(datetime.utcnow())
                action = {
                    '_op_type': args.op_type,
                    '_index': args.index,
                    '_type': args.type,
                    '_id': item.pop('_id'),
                }
                if args.op_type != 'delete':
                    action['_source'] = item
                yield action

    t0 = t00 = time.time()
    i = last_i = 0
    result_counts = {'updated': 0, 'created': 0, 'deleted': 0, 'not_found': 0}
    for i, (success, result) in enumerate(
            elasticsearch.helpers.parallel_bulk(
                client,
                actions=actions(),
                chunk_size=args.chunk_size,
                thread_count=args.threads,
                raise_on_error=False,
            ), start=1):

        result_op = result[args.op_type]['result']
        if args.op_type == 'delete':
            if not success:
                assert result_op == 'not_found', result
        else:
            assert success, (success, result)
        result_counts[result_op] += 1
        t1 = time.time()
        if t1 - t0 > 10:
            _report_stats(i, last_i, t1 - t0, result_counts)
            t0 = t1
            last_i = i
    _report_stats(i, 0, time.time() - t00, result_counts)


def _report_stats(items, prev_items, dt, result_counts):
    print('{items:,} items processed ({stats}) at {speed:.0f} items/s'
          .format(
            items=items,
            stats=', '.join(
                '{}: {:,}'.format(k, v)
                for k, v in sorted(result_counts.items()) if v != 0),
            speed=(items - prev_items) / dt,
    ))
