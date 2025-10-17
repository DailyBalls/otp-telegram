from aiogram.fsm.context import FSMContext

async def reset_fsm(state: FSMContext):
     # Get all stored FSM data
    state_data = await state.get_data()
    
    persistent_data = ["telegram_data"]

    temp_data = {}
    for data in persistent_data:
        temp_data[data] = state_data.get(data)

    # Reset all state data
    await state.clear()
    
    # Restore only the preserved field
    for data in persistent_data:
        if temp_data[data] is not None:
            await state.update_data(**{data: temp_data[data]})