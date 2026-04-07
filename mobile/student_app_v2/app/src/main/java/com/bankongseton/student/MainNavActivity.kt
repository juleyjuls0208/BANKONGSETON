package com.bankongseton.student

import android.content.Intent
import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import androidx.fragment.app.Fragment
import com.google.android.material.bottomnavigation.BottomNavigationView
import com.google.android.material.navigation.NavigationBarView

/**
 * Main navigation hub — hosts bottom nav with 4 destinations:
 * Home, History, Budget, Settings.
 * After v1's activity-back-stack model, v2 uses a fragment-based shell
 * for faster tab switching and no activity churn.
 */
class MainNavActivity : AppCompatActivity() {

    private lateinit var bottomNav: BottomNavigationView

    // Fragments (lazy — created once)
    private val homeFragment by lazy { HomeFragment() }
    private val historyFragment by lazy { HistoryFragment() }
    private val budgetFragment by lazy { BudgetFragment() }
    private val settingsFragment by lazy { SettingsFragment() }

    private var activeFragment: Fragment? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main_nav)

        bottomNav = findViewById(R.id.bottomNav)

        if (savedInstanceState == null) {
            // Attach all fragments hidden initially
            supportFragmentManager.beginTransaction()
                .add(R.id.navHost, settingsFragment, "settings").hide(settingsFragment)
                .add(R.id.navHost, budgetFragment, "budget").hide(budgetFragment)
                .add(R.id.navHost, historyFragment, "history").hide(historyFragment)
                .add(R.id.navHost, homeFragment, "home")
                .commit()
            activeFragment = homeFragment
        } else {
            // Restore active fragment reference
            activeFragment = supportFragmentManager.findFragmentById(R.id.navHost)
        }

        bottomNav.setOnItemSelectedListener(NavigationBarView.OnItemSelectedListener { item ->
            val target = when (item.itemId) {
                R.id.nav_home -> homeFragment
                R.id.nav_history -> historyFragment
                R.id.nav_budget -> budgetFragment
                R.id.nav_settings -> settingsFragment
                else -> return@OnItemSelectedListener false
            }
            switchFragment(target)
            true
        })
    }

    private fun switchFragment(target: Fragment) {
        if (activeFragment === target) return
        supportFragmentManager.beginTransaction()
            .hide(activeFragment!!)
            .show(target)
            .commit()
        activeFragment = target
    }

    /**
     * Called by HomeFragment "See all" to jump to history tab.
     */
    fun selectHistoryTab() {
        bottomNav.selectedItemId = R.id.nav_history
    }
}
