"""
记忆系统 - 调试案例库管理（优化版）
- 添加去重逻辑
- 添加线程安全
- 改进错误处理
"""

import json
import os
import re
import threading
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional

from .logger import get_logger

logger = get_logger("debug-mcp.memory")


class Memory:
    """调试案例记忆系统（优化版）"""

    # 相似度阈值
    SIMILARITY_THRESHOLD = 0.8

    def __init__(self, storage_path: str = None):
        if storage_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            storage_path = os.path.join(
                os.path.dirname(current_dir),
                "cases",
                "debug_cases.json"
            )

        self.storage_path = storage_path
        self.cases: List[Dict] = []
        self._lock = threading.RLock()  # 线程安全锁
        self._ensure_storage_dir()
        self._load()
        logger.info(f"Memory initialized with {len(self.cases)} cases")

    def _ensure_storage_dir(self):
        dir_path = os.path.dirname(self.storage_path)
        if dir_path and not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path, exist_ok=True)
                logger.debug(f"Created storage directory: {dir_path}")
            except OSError as e:
                logger.error(f"Failed to create storage directory: {e}")

    def _load(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.cases = data.get('cases', [])
                logger.debug(f"Loaded {len(self.cases)} cases from storage")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON: {e}")
                self.cases = []
            except IOError as e:
                logger.error(f"Failed to read storage file: {e}")
                self.cases = []

    def _save(self):
        try:
            # 确保目录存在
            self._ensure_storage_dir()

            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump({'cases': self.cases}, f, ensure_ascii=False, indent=2)
            logger.debug(f"Saved {len(self.cases)} cases to storage")
        except IOError as e:
            logger.error(f"Failed to save cases: {e}")
            raise

    def _normalize_text(self, text: str) -> str:
        """文本规范化 - 处理常见缩写和变体"""
        # 转小写
        text = text.lower().strip()

        # 常见缩写规范化
        replacements = {
            r"can't": "cannot",
            r"won't": "will not",
            r"don't": "do not",
            r"doesn't": "does not",
            r"didn't": "did not",
            r"isn't": "is not",
            r"aren't": "are not",
            r"wasn't": "was not",
            r"weren't": "were not",
            r"hasn't": "has not",
            r"haven't": "have not",
            r"hadn't": "had not",
            r"couldn't": "could not",
            r"shouldn't": "should not",
            r"wouldn't": "would not",
            r"'s": " is",
            r"'t": " not",
            r"'re": " are",
            r"'ll": " will",
            r"'ve": " have",
            r"'d": " would",
        }

        for pattern, replacement in replacements.items():
            text = re.sub(pattern, replacement, text)

        # 去除多余空格
        text = re.sub(r'\s+', ' ', text)

        return text

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算两个文本的相似度（增强版）"""
        # 预处理：规范化文本
        t1 = self._normalize_text(text1)
        t2 = self._normalize_text(text2)

        # 提取错误类型和关键信息
        error_type1 = self._extract_error_type(t1)
        error_type2 = self._extract_error_type(t2)

        # 如果错误类型不同，相似度降低
        if error_type1 and error_type2 and error_type1 != error_type2:
            return 0.0

        # 基础相似度
        base_similarity = SequenceMatcher(None, t1, t2).ratio()

        # 关键词重叠奖励
        keywords1 = set(re.findall(r'\b\w{4,}\b', t1))
        keywords2 = set(re.findall(r'\b\w{4,}\b', t2))
        common_keywords = keywords1 & keywords2
        if common_keywords:
            keyword_bonus = len(common_keywords) * 0.05
            base_similarity = min(1.0, base_similarity + keyword_bonus)

        return base_similarity

    def _calculate_quality_score(self, case: Dict) -> float:
        """计算案例质量评分 (0-1)"""
        score = 0.0

        # 有解决方案 +0.3
        if case.get('solution'):
            score += 0.3

        # 有修复代码 +0.3
        if case.get('fix_code') or (case.get('solution') and '```' in case.get('solution', '')):
            score += 0.3

        # 有预防建议 +0.2
        if case.get('prevention'):
            score += 0.2

        # 有根因分析 +0.2
        if case.get('root_cause'):
            score += 0.2

        # 出现次数加分（最多 +0.1）
        occurrences = case.get('occurrences', 0)
        if occurrences > 1:
            score += min(0.1, (occurrences - 1) * 0.02)

        return min(1.0, score)

    def _extract_error_type(self, text: str) -> Optional[str]:
        """提取错误类型"""
        patterns = [
            r'(TypeError|SyntaxError|ReferenceError|ValueError|AttributeError|'
            r'ImportError|OSError|RuntimeError|Error|Exception)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).lower()
        return None

    def _is_duplicate(self, problem: str) -> Optional[str]:
        """
        检查是否已存在相似案例

        Returns:
            存在的案例 ID，如果不存在则返回 None
        """
        problem_lower = problem.lower().strip()

        for case in self.cases:
            existing_problem = case.get('problem', '').lower().strip()
            similarity = self._calculate_similarity(problem_lower, existing_problem)

            if similarity >= self.SIMILARITY_THRESHOLD:
                logger.debug(f"Found duplicate case: {case.get('id')}, similarity: {similarity:.2f}")
                return case.get('id')

        return None

    def add_case(self, case: Dict) -> str:
        """
        添加新案例（带去重）

        Returns:
            案例 ID（新添加的或已存在的）
        """
        with self._lock:
            problem = case.get('problem', '')

            # 检查重复
            existing_id = self._is_duplicate(problem)
            if existing_id:
                logger.info(f"Duplicate case found, incrementing occurrence: {existing_id}")
                self.increment_occurrence(existing_id)
                return existing_id

            # 创建新案例
            case_id = f"case_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
            case['id'] = case_id
            case['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            case['occurrences'] = 1

            self.cases.append(case)
            self._save()

            logger.info(f"Added new case: {case_id}")
            return case_id

    def search(self, keywords: List[str], limit: int = 20) -> List[Dict]:
        """
        搜索案例（带相关性、质量、有效性排序）

        Args:
            keywords: 关键词列表
            limit: 返回结果数量限制

        Returns:
            按相关性排序的案例列表
        """
        if not keywords:
            return []

        keywords_lower = [k.lower() for k in keywords]
        results = []

        for case in self.cases:
            score = 0
            problem = case.get('problem', '').lower()
            case_keywords = [k.lower() for k in case.get('keywords', [])]

            # 关键词匹配计分
            for kw in keywords_lower:
                # 在问题中匹配
                if kw in problem:
                    score += 10

                # 在案例关键词中匹配
                for ck in case_keywords:
                    if kw in ck:
                        score += 5

            if score > 0:
                # 添加质量评分
                quality_score = self._calculate_quality_score(case)

                # 添加用户评分
                user_rating = case.get('user_rating', 0) or 0

                case_with_score = dict(case)
                case_with_score['_search_score'] = score
                case_with_score['_quality_score'] = quality_score
                case_with_score['_user_rating'] = user_rating
                results.append(case_with_score)

        # 按：相关性 × 质量评分 × 用户评分 排序
        results.sort(
            key=lambda x: (
                x.get('_search_score', 0),
                x.get('_quality_score', 0) * (x.get('_user_rating', 0.5) or 0.5),
                x.get('occurrences', 0)
            ),
            reverse=True
        )

        # 移除临时分数字段
        for r in results:
            r.pop('_search_score', None)
            r.pop('_quality_score', None)
            r.pop('_user_rating', None)

        return results[:limit]

    def get_case(self, case_id: str) -> Optional[Dict]:
        """获取指定案例"""
        with self._lock:
            for case in self.cases:
                if case.get('id') == case_id:
                    return case.copy()
            return None

    def update_case(self, case_id: str, updates: Dict) -> bool:
        """更新案例"""
        with self._lock:
            for i, case in enumerate(self.cases):
                if case.get('id') == case_id:
                    self.cases[i].update(updates)
                    self.cases[i]['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    self._save()
                    logger.info(f"Updated case: {case_id}")
                    return True
            return False

    def delete_case(self, case_id: str) -> bool:
        """删除案例"""
        with self._lock:
            for i, case in enumerate(self.cases):
                if case.get('id') == case_id:
                    del self.cases[i]
                    self._save()
                    logger.info(f"Deleted case: {case_id}")
                    return True
            return False

    def increment_occurrence(self, case_id: str):
        """增加案例出现次数"""
        with self._lock:
            for case in self.cases:
                if case.get('id') == case_id:
                    case['occurrences'] = case.get('occurrences', 0) + 1
                    case['last_occurrence'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    self._save()
                    logger.debug(f"Incremented occurrence for case: {case_id}")
                    break

    def mark_effective(self, case_id: str, effective: bool = True) -> bool:
        """
        标记案例解决方案是否有效

        Args:
            case_id: 案例 ID
            effective: True 表示有效，False 表示无效

        Returns:
            是否标记成功
        """
        with self._lock:
            for case in self.cases:
                if case.get('id') == case_id:
                    if effective:
                        case['effective_count'] = case.get('effective_count', 0) + 1
                    else:
                        case['ineffective_count'] = case.get('ineffective_count', 0) + 1

                    # 计算用户评分（有效率）
                    effective_count = case.get('effective_count', 0)
                    ineffective_count = case.get('ineffective_count', 0)
                    total = effective_count + ineffective_count
                    if total > 0:
                        case['user_rating'] = effective_count / total
                    else:
                        case['user_rating'] = None

                    case['last_feedback'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    self._save()
                    logger.info(f"Marked case {case_id} as {'effective' if effective else 'ineffective'}")
                    return True
            return False

    def get_effective_cases(self, min_rating: float = 0.5, limit: int = 20) -> List[Dict]:
        """
        获取高评价的有效解决方案

        Args:
            min_rating: 最低评分阈值 (0-1)
            limit: 返回数量限制
        """
        with self._lock:
            effective_cases = []
            for case in self.cases:
                rating = case.get('user_rating')
                if rating is not None and rating >= min_rating:
                    effective_cases.append(case.copy())

            # 按评分和出现次数排序
            effective_cases.sort(
                key=lambda x: (x.get('user_rating', 0), x.get('occurrences', 0)),
                reverse=True
            )
            return effective_cases[:limit]

    def list_cases(self, limit: int = 20, sort_by: str = "occurrences") -> List[Dict]:
        """
        列出案例

        Args:
            limit: 返回数量限制
            sort_by: 排序字段 (occurrences, created_at, last_occurrence)
        """
        with self._lock:
            if sort_by == "occurrences":
                sorted_cases = sorted(
                    self.cases,
                    key=lambda x: x.get('occurrences', 0),
                    reverse=True
                )
            elif sort_by == "created_at":
                sorted_cases = sorted(
                    self.cases,
                    key=lambda x: x.get('created_at', ''),
                    reverse=True
                )
            elif sort_by == "last_occurrence":
                sorted_cases = sorted(
                    self.cases,
                    key=lambda x: x.get('last_occurrence', ''),
                    reverse=True
                )
            else:
                sorted_cases = self.cases

            return [c.copy() for c in sorted_cases[:limit]]

    def clear(self):
        """清空所有案例"""
        with self._lock:
            count = len(self.cases)
            self.cases = []
            self._save()
            logger.warning(f"Cleared {count} cases from memory")

    def get_stats(self) -> Dict:
        """获取统计信息"""
        with self._lock:
            problem_types = {}
            total_occurrences = 0

            for case in self.cases:
                ptype = case.get('problem_type', 'unknown')
                problem_types[ptype] = problem_types.get(ptype, 0) + 1
                total_occurrences += case.get('occurrences', 0)

            return {
                'total_cases': len(self.cases),
                'total_occurrences': total_occurrences,
                'problem_types': problem_types,
                'unique_problem_types': len(problem_types),
            }

    def get_weekly_report(self) -> Dict:
        """
        获取本周错误报告

        Returns:
            包含本周统计信息的字典
        """
        from datetime import timedelta

        with self._lock:
            today = datetime.now()
            week_ago = today - timedelta(days=7)

            # 本周新增案例
            new_cases = []
            # 本周高频案例
            weekly_counts = {}

            for case in self.cases:
                # 统计本周出现次数
                last_occurrence = case.get('last_occurrence', '')
                if last_occurrence:
                    try:
                        last_time = datetime.strptime(last_occurrence, '%Y-%m-%d %H:%M:%S')
                        if last_time >= week_ago:
                            count = case.get('occurrences', 0)
                            weekly_counts[case.get('id')] = {
                                'problem': case.get('problem', '')[:50],
                                'type': case.get('problem_type', 'unknown'),
                                'count': count
                            }
                    except ValueError:
                        pass

                # 新增案例
                created_at = case.get('created_at', '')
                if created_at:
                    try:
                        created_time = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
                        if created_time >= week_ago:
                            new_cases.append(case)
                    except ValueError:
                        pass

            # 按本周次数排序
            sorted_weekly = sorted(
                weekly_counts.values(),
                key=lambda x: x['count'],
                reverse=True
            )[:10]

            return {
                'week_new_cases': len(new_cases),
                'week_total_occurrences': sum(c.get('count', 0) for c in weekly_counts.values()),
                'top_errors': sorted_weekly,
                'period': f"{(today - timedelta(days=7)).strftime('%Y-%m-%d')} ~ {today.strftime('%Y-%m-%d')}"
            }

    def get_error_trends(self, days: int = 30) -> Dict:
        """
        获取错误趋势分析

        Args:
            days: 统计天数
        """
        with self._lock:
            today = datetime.now()
            start_date = today - timedelta(days=days)

            # 按日期统计
            daily_counts = {}
            problem_types_daily = {}

            for case in self.cases:
                last_occurrence = case.get('last_occurrence', '')
                if last_occurrence:
                    try:
                        last_time = datetime.strptime(last_occurrence, '%Y-%m-%d %H:%M:%S')
                        if last_time >= start_date:
                            date_key = last_time.strftime('%Y-%m-%d')
                            daily_counts[date_key] = daily_counts.get(date_key, 0) + 1

                            ptype = case.get('problem_type', 'unknown')
                            if date_key not in problem_types_daily:
                                problem_types_daily[date_key] = {}
                            problem_types_daily[date_key][ptype] = problem_types_daily[date_key].get(ptype, 0) + 1
                    except ValueError:
                        pass

            # 计算趋势
            if len(daily_counts) >= 2:
                dates = sorted(daily_counts.keys())
                mid_point = len(dates) // 2
                first_half_avg = sum(daily_counts[d] for d in dates[:mid_point]) / mid_point
                second_half_avg = sum(daily_counts[d] for d in dates[mid_point:]) / (len(dates) - mid_point)

                if second_half_avg > first_half_avg * 1.2:
                    trend = "上升"
                elif second_half_avg < first_half_avg * 0.8:
                    trend = "下降"
                else:
                    trend = "平稳"
            else:
                trend = "数据不足"

            # 最常见的问题类型
            type_totals = {}
            for date_types in problem_types_daily.values():
                for ptype, count in date_types.items():
                    type_totals[ptype] = type_totals.get(ptype, 0) + count

            top_types = sorted(type_totals.items(), key=lambda x: x[1], reverse=True)[:5]

            return {
                'period_days': days,
                'total_occurrences': sum(daily_counts.values()),
                'daily_average': round(sum(daily_counts.values()) / max(len(daily_counts), 1), 1),
                'trend': trend,
                'top_problem_types': [{'type': t[0], 'count': t[1]} for t in top_types],
                'daily_counts': daily_counts
            }


# 支持配置的单例
_memory: Optional[Memory] = None
_memory_lock = threading.Lock()


def get_memory(storage_path: str = None, config: Any = None) -> Memory:
    """
    获取 Memory 单例

    Args:
        storage_path: 存储路径
        config: 配置对象（可选）
    """
    global _memory

    if _memory is None:
        with _memory_lock:
            if _memory is None:
                # 如果传入 config，优先使用 config 中的路径
                if config and hasattr(config, 'storage'):
                    if config.storage.path:
                        storage_path = config.storage.path

                _memory = Memory(storage_path)
                logger.info("Created new Memory instance")

    return _memory


def reset_memory():
    """重置 Memory 单例（用于测试）"""
    global _memory
    with _memory_lock:
        if _memory:
            _memory.clear()
        _memory = None
        logger.info("Reset Memory singleton")
