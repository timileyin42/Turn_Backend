"""
Portfolio management service for creating, managing, and exporting user portfolios.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func, desc
from sqlalchemy.orm import selectinload

from app.database.portfolio_models import (
    Portfolio, Achievement, PortfolioItem, SkillAssessment
)
from app.schemas.portfolio_schemas import (
    PortfolioCreate, PortfolioUpdate, PortfolioResponse,
    PortfolioListResponse, AchievementCreate, AchievementUpdate, 
    AchievementResponse, PortfolioItemCreate, PortfolioItemResponse,
    SkillAssessmentCreate, SkillAssessmentResponse, PortfolioAnalyticsResponse
)


class PortfolioService:
    """Service for portfolio management and operations."""
    
    async def create_portfolio(
        self,
        db: AsyncSession,
        user_id: int,
        portfolio_data: PortfolioCreate
    ) -> PortfolioResponse:
        """Create a new portfolio for a user."""
        try:
            # Check if this should be the default portfolio
            if portfolio_data.is_default:
                # Unset other default portfolios for this user
                await db.execute(
                    update(Portfolio)
                    .where(
                        and_(
                            Portfolio.user_id == user_id,
                            Portfolio.is_default == True
                        )
                    )
                    .values(is_default=False)
                )
            
            # Create new portfolio
            db_portfolio = Portfolio(
                user_id=user_id,
                **portfolio_data.model_dump(exclude_unset=True)
            )
            
            db.add(db_portfolio)
            await db.commit()
            await db.refresh(db_portfolio)
            
            return PortfolioResponse.model_validate(db_portfolio)
            
        except Exception as e:
            await db.rollback()
            raise e
    
    async def get_portfolio(
        self,
        db: AsyncSession,
        portfolio_id: int,
        user_id: int
    ) -> Optional[PortfolioResponse]:
        """Get a specific portfolio by ID."""
        result = await db.execute(
            select(Portfolio)
            .options(
                selectinload(Portfolio.items),
                selectinload(Portfolio.achievements)
            )
            .where(
                and_(
                    Portfolio.id == portfolio_id,
                    Portfolio.user_id == user_id
                )
            )
        )
        
        portfolio = result.scalar_one_or_none()
        if not portfolio:
            return None
            
        return PortfolioResponse.model_validate(portfolio)
    
    async def update_portfolio(
        self,
        db: AsyncSession,
        portfolio_id: int,
        user_id: int,
        portfolio_data: PortfolioUpdate
    ) -> Optional[PortfolioResponse]:
        """Update an existing portfolio."""
        try:
            # Check if setting as default
            if portfolio_data.is_default:
                # Unset other default portfolios for this user
                await db.execute(
                    update(Portfolio)
                    .where(
                        and_(
                            Portfolio.user_id == user_id,
                            Portfolio.is_default == True,
                            Portfolio.id != portfolio_id
                        )
                    )
                    .values(is_default=False)
                )
            
            # Update portfolio
            result = await db.execute(
                update(Portfolio)
                .where(
                    and_(
                        Portfolio.id == portfolio_id,
                        Portfolio.user_id == user_id
                    )
                )
                .values(**portfolio_data.model_dump(exclude_unset=True))
                .returning(Portfolio)
            )
            
            portfolio = result.scalar_one_or_none()
            if not portfolio:
                return None
            
            await db.commit()
            await db.refresh(portfolio)
            
            return PortfolioResponse.model_validate(portfolio)
            
        except Exception as e:
            await db.rollback()
            raise e
    
    async def delete_portfolio(
        self,
        db: AsyncSession,
        portfolio_id: int,
        user_id: int
    ) -> bool:
        """Delete a portfolio."""
        try:
            result = await db.execute(
                select(Portfolio).where(
                    and_(
                        Portfolio.id == portfolio_id,
                        Portfolio.user_id == user_id
                    )
                )
            )
            
            portfolio = result.scalar_one_or_none()
            if not portfolio:
                return False
            
            await db.delete(portfolio)
            await db.commit()
            return True
            
        except Exception as e:
            await db.rollback()
            raise e
    
    async def get_user_portfolios(
        self,
        db: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> PortfolioListResponse:
        """Get all portfolios for a user."""
        # Get total count
        count_result = await db.execute(
            select(func.count(Portfolio.id)).where(Portfolio.user_id == user_id)
        )
        total = count_result.scalar()
        
        # Get portfolios
        query = select(Portfolio).options(
            selectinload(Portfolio.items),
            selectinload(Portfolio.achievements)
        ).where(
            Portfolio.user_id == user_id
        ).order_by(desc(Portfolio.updated_at)).offset(skip).limit(limit)
        
        result = await db.execute(query)
        portfolios = result.scalars().all()
        
        portfolio_responses = [
            PortfolioResponse.model_validate(portfolio) 
            for portfolio in portfolios
        ]
        
        return PortfolioListResponse(
            portfolios=portfolio_responses,
            total=total,
            skip=skip,
            limit=limit
        )
    
    async def get_portfolio_analytics(
        self,
        db: AsyncSession,
        portfolio_id: int,
        user_id: int
    ) -> Optional[PortfolioAnalyticsResponse]:
        """Get analytics for a specific portfolio."""
        # Verify ownership
        result = await db.execute(
            select(Portfolio).where(
                and_(
                    Portfolio.id == portfolio_id,
                    Portfolio.user_id == user_id
                )
            )
        )
        
        portfolio = result.scalar_one_or_none()
        if not portfolio:
            return None
        
        # Calculate analytics
        return PortfolioAnalyticsResponse(
            portfolio_id=portfolio_id,
            view_count=portfolio.view_count or 0,
            total_items=len(portfolio.items) if hasattr(portfolio, 'items') else 0,
            total_achievements=len(portfolio.achievements) if hasattr(portfolio, 'achievements') else 0,
            last_updated=portfolio.updated_at,
            is_public=portfolio.is_public,
            public_url=f"/portfolio/{portfolio.public_url_slug}" if portfolio.public_url_slug else None
        )


# Create service instance
portfolio_service = PortfolioService()