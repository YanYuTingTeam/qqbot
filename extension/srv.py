import dns.resolver
from urllib.parse import urlparse

def getsrv(ip):
    """解析域名的srv指向哪里."""
    if "://" in ip:
        domain = urlparse(ip).hostname
    else:
        domain = ip.split(':')[0]
    if not domain:
        return ip
    srv_query = f"_minecraft._tcp.{domain}"
    try:
        answers = dns.resolver.resolve(srv_query, 'SRV')
        records = sorted(answers, key=lambda r: (r.priority, -r.weight))
        if records:
            best_record = records[0]
            target = str(best_record.target).rstrip('.')
            port = best_record.port
            return f"{target}:{port}"
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
        return ip
    except Exception as e:
        print(f"解析失败 {e}")
        return ip
    return ip