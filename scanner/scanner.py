import asyncio
import itertools
import logging
import logging.config
from datetime import datetime
from ipaddress import (
    IPv4Address,
    IPv4Interface,
    IPv4Network,
    ip_network,
    summarize_address_range,
)
from typing import List, Union

import arpreq
import netifaces
from aiodns import DNSResolver
from aiodns.error import DNSError
from icmplib import async_multiping
from log_settings.settings import LoggingContext, logger_config
from mac_vendor_lookup import (
    AsyncMacLookup,
    InvalidMacError,
    MacLookup,
    VendorNotFoundError,
)
from utils import utils

logging.config.dictConfig(logger_config)
logger = logging.getLogger("scanner")


class Devices:
    """
    Поиск активных устройств в сети.
        Поиск происходит порционно. Порция - это сгенерированные ip-адреса из
        подсетей, определенных параметрами exclude и subs. Каждый из адресов
        затем пингуется. По активным адресам определяются mac-адрес, имя хоста,
        название вендора. Размер порции задается параметром chunk_size.
    Параметры
        exclude - список интерфейсов, по сетям которых не стоит искать.
        subs - список подсетей по которым стоит искать.
        chunk_size - размер возвращаемого словаря каждой итерации.
        Если ничего не указано, то поиск по интерфейсам.
        Если только subs, то по подсетям из списка subs.
        Если только exclude, то по интерфейсам, не входящих в список exclude.
        Если указаны subs и exclude, то по комбинациям сетей интерфейсов, не
            входящих в список exclude, и списка в subs.
    Примеры
        devices = Devices(exclude=['lo', 'eth0'])
        devices = Devices(subs=['172.16.41.2/28'])
    """

    def __init__(self, *args, **kwargs):
        _subs_ifaces = self._get_ifaces_subs(kwargs.get("exclude", None))
        _subs = self._get_subs_custom(kwargs.get("subs", None))
        _subs_intersect = self._get_subs_intersect(_subs_ifaces + _subs)
        _chunk_size = kwargs.get("chunk_size", 300)
        self._alives_gen = Scan.get_alives_gen(_subs_intersect, _chunk_size)

    def next_chunk(self) -> List[dict]:
        """
        Возвращает следующую порцию устройств.
        """
        logger.debug("Next chunk started.")
        ips = next(self._alives_gen)
        macs = Scan.get_macs(ips)
        hostnames = asyncio.run(Scan.get_hostnames(ips))
        vendors = asyncio.run(Scan.get_vendors(macs))
        ips_list = list(map(str, ips))
        lengths = len(ips_list), len(macs), len(hostnames), len(vendors)
        try:
            utils.check_inequality(*lengths)
        except utils.ListsNotEqualException as e:
            logger.exception(e)
        devices = utils.to_lists_of_dicts(
            ip=ips, mac=macs, hostname=hostnames, vendor=vendors
        )
        return devices

    def _get_ifaces_subs(self, exclude: List[str] = None) -> List[IPv4Network]:
        ifaces = Interfaces.get_interfaces(exclude)
        ifaces_subs = Subnets.get_ranges_from_ifaces(ifaces)
        return ifaces_subs

    def _get_subs_custom(self, subs: List[str] = None) -> List[IPv4Network]:
        ranges = Subnets.get_ranges_from_str(subs) if subs else []
        return ranges

    def _get_subs_intersect(
        self, subs: List[IPv4Network] = None
    ) -> List[IPv4Network]:
        return Subnets.get_ranges_from_nets(subs)


class Interfaces:
    """
    Работа с интерфейсами.
    """

    @staticmethod
    def get_interfaces(
        exclude: List[IPv4Interface] = None,
    ) -> List[IPv4Interface]:
        """
        Получение системных интерфейсов.
        """
        logger.debug(f"Excluded interfaces {exclude}")
        ifaces = netifaces.interfaces()
        try:
            if not ifaces:
                raise utils.NoInterfaceFoundException
        except Exception:
            logger.exception(f"No network interfaces found.")
        if exclude:
            for iface in exclude:
                ifaces.remove(iface)
        ifconfigs = []
        for iface in ifaces:
            temp = netifaces.ifaddresses(iface).get(netifaces.AF_INET)
            if temp:
                ifconfigs.extend(
                    list(
                        map(
                            lambda x: IPv4Interface(
                                x["addr"] + "/" + x["netmask"]
                            ),
                            temp,
                        )
                    )
                )
        return ifconfigs


class Subnets:
    """
    Работа с подсетями.
    """

    @classmethod
    def get_ranges_from_str(cls, range_addrs: List[str]) -> List[IPv4Network]:
        """
        Получение диапазонов, заданных строкой.
        Например,
        Subnets.get_ranges_from_str(['192.168.1.2/28', '192.168.2-3.1-100'])
        """
        subnetworks = []
        for range_addr in range_addrs:
            if "/" in range_addr:
                subnetworks.extend(
                    list(ip_network(range_addr, strict=False).subnets())
                )
            elif "-" in range_addr:
                first = []
                second = []
                items = range_addr.split(".")
                for item in items:
                    if "-" in item:
                        temp = item.split("-")
                        first.append(temp[0])
                        second.append(temp[1])
                    else:
                        first.append(item)
                        second.append(item)
                first_addr = IPv4Address(".".join(first))
                second_addr = IPv4Address(".".join(second))
                summarized = [
                    ipaddr
                    for ipaddr in summarize_address_range(
                        first_addr, second_addr
                    )
                ]
                subnetworks.extend(summarized)
            else:
                subnetworks.append(IPv4Network(range_addr))
        ranges = cls._remove_subnets(subnetworks)
        return ranges

    @classmethod
    def get_ranges_from_nets(
        cls, subnetworks: List[IPv4Network]
    ) -> List[IPv4Network]:
        """
        Получение уникальных диапазонов из списка диапазонов.
        """
        ranges = cls._remove_subnets(subnetworks)
        return ranges

    def _remove_subnets(ranges: List[IPv4Network]) -> List[IPv4Network]:
        networks_combinations = itertools.combinations(ranges, 2)
        for combination in networks_combinations:
            if combination[0].subnet_of(combination[1]):
                try:
                    ranges.remove(combination[0])
                except:
                    pass
            elif combination[0].supernet_of(combination[1]):
                try:
                    ranges.remove(combination[1])
                except:
                    pass
        return ranges

    @classmethod
    def get_ranges_from_ifaces(
        cls, ifaces: List[IPv4Interface]
    ) -> List[IPv4Network]:
        """
        Получение диапазонов из сетей системных интерфейсов.
        """
        temp_ranges = [IPv4Interface(iface).network for iface in ifaces]
        ranges = cls._remove_subnets(temp_ranges)
        return ranges


class Scan:
    def _get_addresses(network: IPv4Network, chunk_size) -> List[IPv4Address]:
        hosts = network.hosts()
        while True:
            try:
                chunk = itertools.islice(hosts, chunk_size)
                addresses = tuple(map(lambda addr: str(addr), list(chunk)))
                if not addresses:
                    raise StopIteration
                yield addresses
            except StopIteration as e:
                break

    def _arpreq_or_na(host):
        if mac := arpreq.arpreq(host):
            return mac
        else:
            return "N/A"

    @classmethod
    def get_macs(cls, hosts: List[IPv4Address]) -> List[str]:
        logger.debug("Get macs started.")
        macs = map(cls._arpreq_or_na, hosts)
        return list(macs)

    async def _get_hostname(resolver: DNSResolver, address: IPv4Address) -> str:
        try:
            str_ip = str(address)
            temp = await resolver.gethostbyaddr(str_ip)
            result = temp.name
        except DNSError:
            result = "N/A"
        return result

    @classmethod
    async def get_hostnames(cls, ips: List[IPv4Address]) -> List[str]:
        logger.debug("Get hostnames.")
        loop = asyncio.get_running_loop()
        resolver = DNSResolver(loop=loop)
        results = await asyncio.gather(
            *(cls._get_hostname(resolver, ip) for ip in ips)
        )
        return results

    async def _are_alive(addresses: List[IPv4Address]) -> List[IPv4Address]:
        hosts = await async_multiping(
            addresses, count=1, interval=0.2, concurrent_tasks=200
        )
        alive_hosts = list(filter(lambda x: x.is_alive, hosts))
        addresses = list(map(lambda x: IPv4Address(x.address), alive_hosts))
        return addresses

    @classmethod
    def get_alives_gen(
        cls, networks: List[IPv4Network], chunk_size
    ) -> List[IPv4Address]:
        """
        Генератор возвращающий список пигуемых адресов.
        """
        logger.debug("Get alives generator.")
        for network in networks:
            addresses_gen = cls._get_addresses(network, chunk_size)
            try:
                addresses_chunk = next(addresses_gen)
                alives = asyncio.run(
                    cls._are_alive(addresses_chunk), debug=True
                )
                yield alives
            except:
                break

    async def _get_vendor(mac: str) -> str:
        m = AsyncMacLookup()
        try:
            vendor = await m.lookup(mac)
        except (VendorNotFoundError, InvalidMacError, AttributeError):
            vendor = "N/F"
        return vendor

    @classmethod
    async def get_vendors(cls, macs: List[str]) -> List[str]:
        logger.debug("Get vendors.")
        results = list(map(cls._get_vendor, macs))
        return await asyncio.gather(*results)
