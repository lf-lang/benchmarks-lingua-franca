target_include_directories(${LF_MAIN_TARGET} PUBLIC ${CMAKE_CURRENT_LIST_DIR}/include)
target_sources(${LF_MAIN_TARGET} PRIVATE ${CMAKE_CURRENT_LIST_DIR}/lib/matrix.c)
target_link_libraries(${LF_MAIN_TARGET} PRIVATE m)
target_compile_definitions(reactor-uc PUBLIC LF_LOG_LEVEL_ALL=0)