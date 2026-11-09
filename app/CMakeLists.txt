if(BUILD_TESTS)
    message(STATUS "Configuring tests for app module")

    add_executable(version_check_test
        core/src/version_check.c
        core/test/version_check_test.cpp
    )
    target_include_directories(version_check_test PRIVATE 
        core/inc
    )
    target_link_libraries(version_check_test PRIVATE 
        GTest::gtest_main 
        GTest::gmock
    )
    gtest_discover_tests(version_check_test)

    add_executable(shell_test
        shell/src/shell.c
        shell/test/shell_test.cpp
    )
    target_include_directories(shell_test PRIVATE 
        shell/Include
    )
    target_link_libraries(shell_test PRIVATE 
        GTest::gtest_main 
        GTest::gmock
    )
    gtest_discover_tests(shell_test)

else()
    cmake_minimum_required(VERSION 3.22)

    target_include_directories(${PROJECT_NAME} PUBLIC 
        ${CMAKE_CURRENT_SOURCE_DIR}/core/inc
        ${CMAKE_CURRENT_SOURCE_DIR}/shell/Include
    )

    target_sources(${PROJECT_NAME} PRIVATE
        core/src/app.c
        core/src/shell_commands.c
        core/src/retarget.c
        core/src/wrapper.c
        core/src/version_check.c
        shell/src/shell.c
    )
endif()
