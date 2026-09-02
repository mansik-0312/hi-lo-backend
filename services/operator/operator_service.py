from typing import Any, Dict

from fastapi import HTTPException, status

from config.models.operator_model import (
    OperatorRepository,
)

from schemas.operator.operator_schema import (
    OperatorCreateRequest,
    OperatorUpdateRequest,
)


class OperatorService:
    """
    Service responsible for operator business logic.
    """

    @staticmethod
    async def create_operator(
        payload: OperatorCreateRequest,
    ) -> Dict[str, Any]:
        """
        Create a new operator.
        """

        existing_operator = (
            await OperatorRepository.get_by_code(
                payload.operator_code
            )
        )

        if existing_operator:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Operator with this operator_code "
                    "already exists."
                ),
            )

        operator_data = payload.model_dump()

        operator_id = (
            await OperatorRepository.create(
                operator_data
            )
        )

        operator = (
            await OperatorRepository.get_by_id(
                operator_id
            )
        )

        if not operator:
            raise HTTPException(
                status_code=(
                    status.HTTP_500_INTERNAL_SERVER_ERROR
                ),
                detail=(
                    "Operator was created but could "
                    "not be retrieved."
                ),
            )

        return OperatorService._serialize_operator(
            operator
        )

    @staticmethod
    async def get_operator(
        operator_id: str,
    ) -> Dict[str, Any]:
        """
        Retrieve an operator by ID.
        """

        operator = (
            await OperatorRepository.get_by_id(
                operator_id
            )
        )

        if not operator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Operator not found.",
            )

        return OperatorService._serialize_operator(
            operator
        )

    @staticmethod
    async def update_operator(
        operator_id: str,
        payload: OperatorUpdateRequest,
    ) -> Dict[str, Any]:
        """
        Update an existing operator.
        """

        existing_operator = (
            await OperatorRepository.get_by_id(
                operator_id
            )
        )

        if not existing_operator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Operator not found.",
            )

        update_data = payload.model_dump(
            exclude_unset=True
        )

        if update_data:
            updated = (
                await OperatorRepository.update(
                    operator_id,
                    update_data,
                )
            )

            if not updated:
                raise HTTPException(
                    status_code=(
                        status.HTTP_500_INTERNAL_SERVER_ERROR
                    ),
                    detail=(
                        "Failed to update operator."
                    ),
                )

        operator = (
            await OperatorRepository.get_by_id(
                operator_id
            )
        )

        if not operator:
            raise HTTPException(
                status_code=(
                    status.HTTP_500_INTERNAL_SERVER_ERROR
                ),
                detail=(
                    "Operator could not be retrieved "
                    "after update."
                ),
            )

        return OperatorService._serialize_operator(
            operator
        )

    @staticmethod
    def _serialize_operator(
        operator: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Convert MongoDB operator document into
        API response format.
        """

        return {
            "id": str(operator["_id"]),
            "operator_code": operator[
                "operator_code"
            ],
            "name": operator["name"],
            "status": operator.get(
                "status",
                "active",
            ),
            "default_currency": operator[
                "default_currency"
            ],
            "configuration": operator.get(
                "configuration",
                {},
            ),
            "created_at": operator[
                "created_at"
            ],
            "updated_at": operator[
                "updated_at"
            ],
        }