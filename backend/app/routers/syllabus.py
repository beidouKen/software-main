from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import datetime
from app import models, schemas
from app.dependencies import get_db, get_current_user

router = APIRouter()

def delete_tag_and_children(db: Session, tag_id: int):
    """递归删除标签及其所有子标签"""
    # 先删除所有子标签
    children = db.query(models.KnowledgeTag).filter(models.KnowledgeTag.parent_id == tag_id).all()
    for child in children:
        delete_tag_and_children(db, child.id)
    # 删除当前标签
    tag = db.query(models.KnowledgeTag).filter(models.KnowledgeTag.id == tag_id).first()
    if tag:
        db.delete(tag)

def build_tag_tree(tags: List[models.KnowledgeTag], parent_id: Optional[int] = None) -> List[dict]:
    """构建树形结构"""
    result = []
    for tag in tags:
        if tag.parent_id == parent_id:
            tag_dict = {
                "id": tag.id,
                "name": tag.name,
                "content": tag.content,
                "parent_id": tag.parent_id,
                "teacher_id": tag.teacher_id,
                "order": tag.order,
                "created_at": tag.created_at.isoformat() if tag.created_at else None,
                "updated_at": tag.updated_at.isoformat() if tag.updated_at else None,
                "children": build_tag_tree(tags, tag.id)
            }
            result.append(tag_dict)
    # 按order排序
    result.sort(key=lambda x: x["order"])
    return result

@router.get("/tags")
def get_tags(
    db: Session = Depends(get_db),
    current_user_data: dict = Depends(get_current_user)
):
    """获取当前教师的所有标签（树形结构）"""
    user_type = current_user_data.get("user_type")
    if user_type != "teacher":
        raise HTTPException(
            status_code=403, 
            detail=f"Only teachers can access this resource. Current user type: {user_type}"
        )
    
    teacher = current_user_data["user"]
    tags = db.query(models.KnowledgeTag).filter(
        models.KnowledgeTag.teacher_id == teacher.id
    ).all()
    
    # 构建树形结构
    tree = build_tag_tree(tags, None)
    return tree

@router.post("/tags")
def create_tag(
    tag: schemas.KnowledgeTagCreate,
    db: Session = Depends(get_db),
    current_user_data: dict = Depends(get_current_user)
):
    """创建标签"""
    user_type = current_user_data.get("user_type")
    if user_type != "teacher":
        raise HTTPException(
            status_code=403, 
            detail=f"Only teachers can access this resource. Current user type: {user_type}"
        )
    
    teacher = current_user_data["user"]
    
    # 如果指定了parent_id，验证父标签是否存在且属于当前教师
    if tag.parent_id:
        parent_tag = db.query(models.KnowledgeTag).filter(
            and_(
                models.KnowledgeTag.id == tag.parent_id,
                models.KnowledgeTag.teacher_id == teacher.id
            )
        ).first()
        if not parent_tag:
            raise HTTPException(status_code=404, detail="Parent tag not found")
    
    # 创建新标签
    db_tag = models.KnowledgeTag(
        name=tag.name,
        content=tag.content,
        parent_id=tag.parent_id,
        teacher_id=teacher.id,
        order=tag.order or 0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    
    return {
        "id": db_tag.id,
        "name": db_tag.name,
        "content": db_tag.content,
        "parent_id": db_tag.parent_id,
        "teacher_id": db_tag.teacher_id,
        "order": db_tag.order,
        "created_at": db_tag.created_at.isoformat() if db_tag.created_at else None,
        "updated_at": db_tag.updated_at.isoformat() if db_tag.updated_at else None,
        "children": []
    }

@router.put("/tags/{tag_id}")
def update_tag(
    tag_id: int,
    tag_update: schemas.KnowledgeTagUpdate,
    db: Session = Depends(get_db),
    current_user_data: dict = Depends(get_current_user)
):
    """更新标签"""
    user_type = current_user_data.get("user_type")
    if user_type != "teacher":
        raise HTTPException(
            status_code=403, 
            detail=f"Only teachers can access this resource. Current user type: {user_type}"
        )
    
    teacher = current_user_data["user"]
    
    db_tag = db.query(models.KnowledgeTag).filter(
        and_(
            models.KnowledgeTag.id == tag_id,
            models.KnowledgeTag.teacher_id == teacher.id
        )
    ).first()
    
    if not db_tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    # 更新字段
    if tag_update.name is not None:
        db_tag.name = tag_update.name
    if tag_update.content is not None:
        db_tag.content = tag_update.content
    if tag_update.order is not None:
        db_tag.order = tag_update.order
    
    db_tag.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_tag)
    
    # 获取子标签
    children = db.query(models.KnowledgeTag).filter(
        models.KnowledgeTag.parent_id == tag_id
    ).all()
    children_list = [{
        "id": child.id,
        "name": child.name,
        "content": child.content,
        "parent_id": child.parent_id,
        "teacher_id": child.teacher_id,
        "order": child.order,
        "created_at": child.created_at.isoformat() if child.created_at else None,
        "updated_at": child.updated_at.isoformat() if child.updated_at else None,
        "children": []
    } for child in children]
    
    return {
        "id": db_tag.id,
        "name": db_tag.name,
        "content": db_tag.content,
        "parent_id": db_tag.parent_id,
        "teacher_id": db_tag.teacher_id,
        "order": db_tag.order,
        "created_at": db_tag.created_at.isoformat() if db_tag.created_at else None,
        "updated_at": db_tag.updated_at.isoformat() if db_tag.updated_at else None,
        "children": children_list
    }

@router.delete("/tags/{tag_id}")
def delete_tag(
    tag_id: int,
    db: Session = Depends(get_db),
    current_user_data: dict = Depends(get_current_user)
):
    """删除标签及其所有子标签"""
    user_type = current_user_data.get("user_type")
    if user_type != "teacher":
        raise HTTPException(
            status_code=403, 
            detail=f"Only teachers can access this resource. Current user type: {user_type}"
        )
    
    teacher = current_user_data["user"]
    
    db_tag = db.query(models.KnowledgeTag).filter(
        and_(
            models.KnowledgeTag.id == tag_id,
            models.KnowledgeTag.teacher_id == teacher.id
        )
    ).first()
    
    if not db_tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    # 递归删除标签及其所有子标签
    delete_tag_and_children(db, tag_id)
    db.commit()
    
    return {"message": "Tag deleted successfully"}

