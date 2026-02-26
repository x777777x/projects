export const isTaskOverdue = (start, end, status) => {
    if (!start && !end) return false;
    if (status === '已完成') return false;

    // 获取今天的日期字符串 YYYY-MM-DD
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    const todayStr = `${year}-${month}-${day}`;

    if (start && end) {
        if (start <= todayStr && todayStr <= end && status === '未开始') {
            return true;
        } else if (todayStr > end && status !== '已完成') {
            return true;
        }
    } else if (end) {
        if (todayStr > end && status !== '已完成') {
            return true;
        }
    } else if (start) {
        if (start <= todayStr && status === '未开始') {
            return true;
        }
    }

    return false;
}
