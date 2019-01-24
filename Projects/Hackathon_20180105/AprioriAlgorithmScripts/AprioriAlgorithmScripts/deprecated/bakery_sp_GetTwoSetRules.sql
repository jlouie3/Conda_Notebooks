-- ================================================
-- Template generated from Template Explorer using:
-- Create Procedure (New Menu).SQL
--
-- Use the Specify Values for Template Parameters 
-- command (Ctrl-Shift-M) to fill in the parameter 
-- values below.
--
-- This block of comments will not be included in
-- the definition of the procedure.
-- ================================================
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
-- =============================================
-- Author:		Jon Louie
-- Create date: 1/1/2019
-- Description:	Generate two-set rules for items above the support and confidence thresholds
-- =============================================
CREATE PROCEDURE sp_Bakery_GetTwoSetRules
	@min_support DECIMAL(19,9) = .005,
	@min_confidence DECIMAL(19,9) = 2.5
AS
BEGIN
	SET NOCOUNT ON;

	SELECT 
		ItemId1, 
		ItemId2, 
		Confidence
		--Item1Support
		--Item2Support
		--Lift = Confidence / Item2Support
	FROM fn_Bakery_CalculateTwoSetConfidence(@min_support)
	WHERE Confidence >= @min_confidence
END
GO
