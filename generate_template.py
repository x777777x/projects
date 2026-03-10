import pandas as pd
import os

def create_template():
    output_path = r'd:\开发项目\projects\frontend\public\项目模板.xlsx'
    
    # 确保目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 定义表头
    columns = [
        "编号", "里程碑", "一级任务", "二级任务", 
        "责任部门", "工期", "开始时间", "结束时间", 
        "状态", "备注"
    ]
    
    # 创建包含表头和第一行项目名称的DataFrame
    # 第二行为列头
    data = {
        "编号": ["项目名称：测试项目（请确保第一行是项目名称，本行说明文字可在此单元格替换）"],
        "里程碑": [""],
        "一级任务": [""],
        "二级任务": [""],
        "责任部门": [""],
        "工期": [""],
        "开始时间": [""],
        "结束时间": [""],
        "状态": [""],
        "备注": [""]
    }
    
    # Actually, the requirement says:
    # 1. 第一行必须是项目名称。
    # 2. 第二行为列头，必须严格按照以下顺序和名称：编号、里程碑、一级任务、二级任务、责任部门、工期、开始时间、结束时间、状态、备注。
    # Let's create an excel file that matches exactly this matrix.
    
    matrix = [
        ["请在这里填写项目名称", "", "", "", "", "", "", "", "", ""], # 第一行
        columns # 第二行 (表头)
    ]
    
    df = pd.DataFrame(matrix)
    
    # Write to Excel without header and index
    df.to_excel(output_path, index=False, header=False)
    print(f"Template successfully generated at {output_path}")

if __name__ == '__main__':
    create_template()
