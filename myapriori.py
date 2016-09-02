#!/usr/bin/python
# -*- coding:utf-8 -*-
from itertools import combinations


def load_data_set():
    '''
    Returns:
    --------
    like this: [[1, 3, 4], [2, 3, 5], [1, 2, 3, 5], [2, 5]]
    '''
    with open("order2016-08-31") as fp:
        itemid_list = []
        for line in fp:
            order_id, order_lst = line.rstrip('\n').split('\t')
            order_lst = eval(order_lst)
            if len(order_lst) > 1:
                order_lst = [int(itemid) for itemid in order_lst]
                itemid_list.append(order_lst)
    return itemid_list


def subtract_item_set(pre_discard_itemset, candidate_set):
    '''
    首先去除候选集中不符合非频繁项集的那些元素，
    在当前候选集中去掉上一轮删除的项集，
    比如{2, 3}是非频繁项集，那么就将删除candidate_set中的{2, 3, x}这些项集

    Parameters:
    -----------
    pre_discard_itemset: 上一轮删除的项集

    candidate_set: 上一次产生的候选集

    Returns:
    --------
    返回经过pre_discard_itemset筛选后的项集列表
    '''
    saved_item_set = set()
    discard_item_set = set()
    for item in candidate_set:
        is_discard = False
        for d_item in pre_discard_itemset:
            if d_item.issubset(item):
                is_discard = True
        if is_discard:
            discard_item_set.add(tuple(item))
        else:
            saved_item_set.add(tuple(item))
    # saved_item_set, discard_item_set
    return [set(i) for i in saved_item_set], [set(i) for i in discard_item_set]


def scan_data_set(data_set, candidate_set, min_support):
    '''
    扫描一遍数据集，从候选集中挑出满足支持度的频繁项集，
    同时记录每个项集的支持度（供后面置信度计算）
    '''
    data_set = [set(i) for i in data_set]
    data_set_size = len(data_set)
    candidate_set_size = len(candidate_set)
    cand_set_count = [0 for i in range(candidate_set_size)]

    # 对候选集中的元素通过遍历数据集得到他们出现的次数
    for i in range(candidate_set_size):
        for ds in data_set:
            if candidate_set[i].issubset(ds):
                cand_set_count[i] += 1

    saved_item_set = []
    discard_item_set = []
    support_data = []
    # 删除不满足支持度的
    for i in range(candidate_set_size):
        support = cand_set_count[i] * 1.0 / data_set_size
        if support >= min_support:
            saved_item_set.append(candidate_set[i])
            support_data.append(support)
        else:
            discard_item_set.append(candidate_set[i])
    return saved_item_set, discard_item_set, support_data


def gen_cand_set(data_set, previous_freq_set, k):
    '''
    从上一次生成的候选集中产生本次的候选集（未经过支持度筛选处理的），
    只是单纯生成下一轮的组合集

    Parameters:
    -----------
    data_set: 数据集，用以生成k为1的项集

    previous_freq_set: 上一次产生的候选集

    k: 本次产生的候选集中项目的大小

    Returns:
    --------
    返回列表存储的项集，每个项集是一个集合set, [{0}, {1}, {2}, {3}, {4}...]
    '''
    if k == 1:
        # 列表解析
        item_set = set([item for sublist in data_set for item in sublist])  # 或者item_set = set(sum(data_set, []))
        return [set([i]) for i in item_set]
    elif k > 1:
        cur_freq_set = set()
        pre_fre_set_len = len(previous_freq_set)
        for i in range(pre_fre_set_len):
            for j in range(i + 1, pre_fre_set_len):
                # 遍历所有的两两组合，并将其加入到集合中
                # {(1, 2, 3), (1, 3, 5), (2, 3, 4)}
                s = previous_freq_set[i] | previous_freq_set[j]
                if len(s) == k:
                    cur_freq_set.add(tuple(s))
    return [set(i) for i in cur_freq_set]


def gen_frequecy_set(data_set, min_support):
    '''
    生成频繁项集

    Returns:
    --------
    freq_item_set: [[set(item1), set(item2)..]...] 存储频繁项集
    item_set_support: [[support_score1, s_score2..]] 每个项集对应的支持度分值
    '''
    freq_item_set = []
    item_set_support = []
    discard_item_set = None
    cur_dis_item_set_1, cur_dis_item_set_2 = [], []
    cur_item_set_size = 0
    while True:
        # 循环产生项集大小为1, 2...的项集
        cur_item_set_size += 1
        if cur_item_set_size == 1:
            # 产生初始的候选集
            cur_candiate_set = gen_cand_set(data_set, [], cur_item_set_size)
            # 将候选集分成要满足支持度的集合和不满足支持度的集合，同时记录满足支持度集合对应的支持度分值
            saved_item_set, cur_dis_item_set_1, support_data = scan_data_set(data_set, cur_candiate_set, min_support)
        else:
            # 生成该轮候选集
            cur_candiate_set = gen_cand_set(data_set, freq_item_set[-1], cur_item_set_size)
            # 去除候选集中不符合非频繁项集的那些元素
            cur_candiate_set, cur_dis_item_set_1 = subtract_item_set(discard_item_set, cur_candiate_set)
            # 对剩下的候选集，进行遍历数据集，得到保存、丢弃、支持度集合
            saved_item_set, cur_dis_item_set_2, support_data = scan_data_set(data_set, cur_candiate_set, min_support)
        if saved_item_set == []:  # 如果该轮没有产生任何频繁项集，则下一轮也不会产生新的频繁项集了，退出
            break
        freq_item_set.append(saved_item_set)  # freq_item_set存储每一轮产生的频繁项集

        discard_item_set = cur_dis_item_set_1  # discard_item_set存储每一轮产生的要丢弃的项集
        discard_item_set.extend(cur_dis_item_set_2)

        item_set_support.append(support_data)  # item_set_support存储每一轮产生的频繁项集对应的支持度值
    return freq_item_set, item_set_support


def gen_association_rules(freq_item_set, support_data, min_confd):
    '''
    生成关联规则

    Returns:
    --------
    association_rules: [(set(item1, item2, ...), itemx, confidence_score), ..]
    存储关联规则，list存储，每个元素都是一个3元组，分别表示item1 和 item2.. 推出 itemx，置信度为confidence_score
    '''
    association_rules = []
    for i in range(1, len(freq_item_set)):
        for freq_item in freq_item_set[i]:  # 对频繁项集的每一项尝试生成关联规则
            gen_rules(freq_item, support_data, min_confd, association_rules)
    return association_rules


def gen_rules(freq_item, support_data, min_confd, association_rules):
    '''
    生成关联规则，然后存储到association_rules中
    '''
    if len(freq_item) >= 2:  # 遍历二阶及以上的频繁项集
        for i in range(1, len(freq_item)):  # 生成多种关联规则
            for item in combinations(freq_item, i):  # 遍历长度为1的item的组合
                conf = support_data[frozenset(freq_item)] / float(support_data[frozenset(freq_item) - frozenset(item)])
                if conf >= min_confd:
                    association_rules.append((freq_item - set(item), item, conf))
                    gen_rules(freq_item - set(item), support_data, min_confd, association_rules)


def support_map(freq_item_set, item_set_support):
    '''
    将生成的频繁项集和每个项集对应的支持度对应起来

    Returns:
    --------
    support_data: {frozenset(item1, item2..): support_score, ..}
    '''
    support_data = {}
    for i in range(len(freq_item_set)):
        for j in range(len(freq_item_set[i])):
            support_data[frozenset(freq_item_set[i][j])] = item_set_support[i][j]
    return support_data


def apriori_gen_rules(data_set, min_support, min_confd):
    '''
    利用apriori算法生成关联规则分为两步：
    Step1：生成频繁项集
    Step2：生成关联规则

    Parameters:
    -----------
    data_set: item list

    min_support: 项集需要满足的最小支持度，|X U Y| / |All|

    min_confd: 项集之间关系需要满足的最小置信度，|X U Y| / |X|

    Returns:
    --------
    rules: 通过apriori算法挖掘出的关联规则
    '''
    freq_item_set, item_set_support = gen_frequecy_set(data_set, min_support)  # 利用Apriori算法生成频繁项集和对应的支持度
    support_data = support_map(freq_item_set, item_set_support)  # 将频繁项集和支持度联系起来
    rules = gen_association_rules(freq_item_set, support_data, min_confd)  # 利用频繁项集、对应的支持度和置信度生成关联规则
    return rules


if __name__ == '__main__':
    data_set = load_data_set()
    min_support = 0.004  # 最小支持度
    min_confd = 0.05  # 可信度或支持度
    rules = apriori_gen_rules(data_set=data_set, min_support=min_support, min_confd=min_confd)
    print sorted(rules, key=lambda x: x[2], reverse=True)[15: ]
